# -*- coding: utf-8 -*-

import datetime
import logging
import time
import random
import decimal
from django.db import transaction
from django.db.models import Sum, Count, F
from django.utils.encoding import smart_unicode
from django.conf import settings

from common import utils, debug, validators, cache, raw_sql
from www.misc.decorators import cache_required
from www.misc import consts

from www.service.models import Kind, KindOpenInfo, Service, Product, Order, Zan

DEFAULT_DB = 'default'

dict_err = {
    20101: u'该类别下已有同名供应商',
    20102: u'赞一次就可以了，多了会骄傲',
    20103: u'没有找到对应的供应商',

    20201: u'没有找到对应的产品',
    20202: u'已存在同名的产品',

    20301: u'正在预约供应商，无需多次提交',
}
dict_err.update(consts.G_DICT_ERROR)


class KindBase(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    # @cache_required(cache_key='kind_list_%s', expire=3600 * 12, cache_key_type="city_id")
    def get_kind_list(self, city_id=1974):
        """
        @note:获取首页所需列表
        data = [
            (0, u"餐饮福利", u"下午茶、生日会、工作餐、礼品", True, [
                {"id": 1, "name": u"下午茶", "is_open": True, "is_new": True},
            ]),
        ]
        """
        data = []
        kois = list(KindOpenInfo.objects.filter(city_id=city_id))

        def _get_kind_open(kind):
            for koi in kois:
                if koi.kind_id == kind.id:
                    return koi

        for kt in Kind.kind_type_choices:
            is_new_total = False
            ks = []
            kinds = Kind.objects.filter(kind_type=kt[0], state=True)
            lst_kind_name = []
            for kind in kinds:
                koi = _get_kind_open(kind)
                is_new = True if koi and koi.open_time.date() >= (datetime.datetime.now().date() - datetime.timedelta(days=7)) else False
                if is_new:
                    is_new_total = True
                ks.append(dict(id=kind.id, name=kind.name, is_open=True if koi else False, is_new=is_new, url=kind.get_url()))
                lst_kind_name.append(kind.name)

            big_kind_summary = u"、".join(lst_kind_name[:3]) + (u" ..." if len(lst_kind_name) > 3 else "")
            ls = [kt[0], kt[1], big_kind_summary, is_new_total, ks]
            data.append(ls)

        return data

    def get_kind_by_id(self, kind_id):
        try:
            return Kind.objects.get(id=kind_id)
        except Service.DoesNotExist:
            return ''

    def get_all_kinds(self, state=True):
        objs = Kind.objects.all()

        if state is not None:
            objs = objs.filter(state=state)

        return objs

    def search_kinds_for_admin(self, name='', state=True):
        objs = self.get_all_kinds(state)

        if name:
            objs = objs.filter(name__icontains=name)

        return objs

    def modify_kind(self, kind_id, name, kind_type, hot, sort, state, slogan):
        if not (kind_id and name and kind_type and hot and sort and state and slogan):
            return 99800, dict_err.get(99800)

        obj = self.get_kind_by_id(kind_id)
        if not obj:
            return 20102, dict_err.get(20102)

        try:
            obj.name = name
            obj.kind_type = kind_type
            obj.hot = hot
            obj.sort = sort
            obj.state = int(state)
            obj.slogan = slogan
            obj.save()

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def add_kind(self, name, kind_type, hot, sort, state, slogan):
        if not (name and kind_type and hot and sort and state and slogan):
            return 99800, dict_err.get(99800)

        try:
            obj = Kind.objects.create(
                name=name,
                kind_type=kind_type,
                hot=hot,
                sort=sort,
                state=int(state),
                slogan=slogan
            )
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def get_kinds_by_name(self, name):
        objs = self.get_all_kinds()

        if name:
            objs = objs.filter(name__icontains=name)

        return objs[:10]


class ServiceBase(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    def add_service(self, name, kind_id, logo, city_id, summary, des, imgs, service_area,
                    tel=None, addr=None, longitude=None, latitude=None, join_time=None, recommend_user_id=None,
                    recommend_des=None, level=0, is_show=True, sort=0):
        if Service.objects.filter(name=name, kind=kind_id):
            return 20101, dict_err.get(20101)

        try:
            assert all([logo, city_id, summary, des, imgs, service_area])
        except Exception, e:
            return 99800, dict_err.get(99800)

        service = Service.objects.create(name=name, kind_id=kind_id, logo=logo, city_id=city_id, summary=summary, des=des,
                                         imgs=imgs, service_area=service_area, tel=tel, addr=addr, longitude=longitude, latitude=latitude,
                                         join_time=join_time, recommend_user_id=recommend_user_id, recommend_des=recommend_des,
                                         level=level, is_show=is_show, sort=sort)

        return 0, service

    def get_service_by_kind(self, kind, state=True):
        ps = dict(kind=kind)
        if state is not None:
            ps.update(dict(state=state))

        return Service.objects.select_related("kind").filter(**ps)

    def get_service_by_id(self, service_id):
        try:
            return Service.objects.select_related("kind").get(id=service_id)
        except Service.DoesNotExist:
            return ''

    def add_zan_count(self, service_id):
        Service.objects.filter(id=service_id).update(zan_count=F('zan_count') + 1)

    def add_order_count(self, service_id):
        Service.objects.filter(id=service_id).update(order_count=F('order_count') + 1)

    def minus_zan_count(self, service_id):
        Service.objects.filter(id=service_id).update(zan_count=F('zan_count') - 1)

    def minus_order_count(self, service_id):
        Service.objects.filter(id=service_id).update(order_count=F('order_count') - 1)

    def get_all_services(self, state=True):
        objs = Service.objects.all()

        if state is not None:
            objs = objs.filter(state=state)

        return objs

    def search_services_for_admin(self, name, state):
        objs = self.get_all_services(state)

        if name:
            objs = objs.filter(name__icontains=name)

        return objs

    def add_service(self, name, kind, logo, city, summary, des, imgs,
                    service_area, tel='', addr='', longitude='', latitude='', join_time='', recommend_user_id='',
                    recommend_des='', zan_count=0, order_count=0, level=0, is_show=True, state=True, sort=0):

        if not (name and kind and logo and city and summary and des and imgs):
            return 99800, dict_err.get(99800)

        if Service.objects.filter(name=name):
            return 20201, dict_err.get(20201)

        try:
            obj = Service.objects.create(
                name=name,
                kind_id=kind,
                logo=logo,
                city_id=city,
                summary=summary,
                des=des,
                imgs=imgs,
                service_area=service_area,
                tel=tel,
                addr=addr,
                longitude=longitude,
                latitude=latitude,
                join_time=join_time,
                recommend_user_id=recommend_user_id,
                recommend_des=recommend_des,
                zan_count=zan_count,
                order_count=order_count,
                level=level,
                is_show=is_show,
                state=int(state),
                sort=sort
            )
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def modify_service(self, obj_id, name, kind, logo, city, summary, des, imgs,
                       service_area, tel='', addr='', longitude='', latitude='', join_time='', recommend_user_id='',
                       recommend_des='', zan_count=0, order_count=0, level=0, is_show=True, state=True, sort=0):

        if not (obj_id and name and kind and logo and city and summary and des and imgs):
            return 99800, dict_err.get(99800)

        obj = self.get_service_by_id(obj_id)
        if not obj:
            return 20103, dict_err.get(20103)

        if obj.name != name and Service.objects.filter(name=name):
            return 20201, dict_err.get(20201)

        # import re
        # imgs_str = ''.join(re.compile('<img .*?src=[\"\'](.+?)[\"\']').findall(imgs))

        try:
            obj.name = name
            obj.kind_id = kind
            obj.logo = logo
            obj.city_id = city
            obj.summary = summary
            obj.des = des
            obj.imgs = imgs
            obj.service_area = service_area
            obj.tel = tel
            obj.addr = addr
            obj.longitude = longitude
            obj.latitude = latitude
            obj.join_time = join_time
            obj.recommend_user_id = recommend_user_id
            obj.recommend_des = recommend_des
            obj.zan_count = zan_count
            obj.order_count = order_count
            obj.level = level
            obj.is_show = int(is_show)
            obj.state = int(state)
            obj.sort = sort
            obj.save()
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def get_services_by_name(self, name):
        objs = self.get_all_services()

        if name:
            objs = objs.filter(name__icontains=name)

        return objs[:10]


class ProductBase(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    def add_product(self, name, service_id, des, price, cover=None, summary=None):
        try:
            assert all([name, service_id, des, price])
        except:
            return 99800, dict_err.get(99800)

        if Product.objects.filter(name=name, service=service_id):
            return 99802, dict_err.get(99802)

        product = Product.objects.create(
            name=name,
            service_id=service_id,
            des=des,
            price=price,
            cover=cover,
            summary=summary
        )

        return 0, product

    def get_products_by_service(self, service):
        return Product.objects.select_related("service").filter(service=service, state=True)

    def get_product_by_id(self, product_id):
        try:
            return Product.objects.select_related("service").get(id=product_id)
        except Service.DoesNotExist:
            return None

    def get_all_products(self, state=True):
        objs = Product.objects.all()

        if state is not None:
            objs = objs.filter(state=state)

        return objs

    def search_products_for_admin(self, name, state):
        objs = self.get_all_products(state)

        if name:
            objs = objs.filter(name__icontains=name)

        return objs

    def modify_product(self, obj_id, name, service, cover, summary, des, price,
                       params='', state=True, sort=0):

        if not (obj_id and name and service and cover and summary and des and price):
            return 99800, dict_err.get(99800)

        obj = self.get_product_by_id(obj_id)
        if not obj:
            return 20201, dict_err.get(20201)

        if obj.name != name and Product.objects.filter(name=name):
            return 20202, dict_err.get(20202)

        try:
            obj.name = name
            obj.service_id = service
            obj.cover = cover
            obj.summary = summary
            obj.des = des
            obj.price = price
            obj.params = params
            obj.state = int(state)
            obj.sort = sort
            obj.save()
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)


class ZanBase(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    @transaction.commit_manually
    def add_zan(self, user_id, service_id):
        try:
            assert all([user_id, service_id])
        except:
            transaction.rollback()
            return 99800, dict_err.get(99800)

        if Zan.objects.filter(user_id=user_id, service=service_id):
            transaction.rollback()
            return 20102, dict_err.get(20102)

        try:
            zan = Zan.objects.create(user_id=user_id, service_id=service_id)
            ServiceBase().add_zan_count(service_id)
            zan_count = zan.service.zan_count
            transaction.commit()
            # return 0, dict_err.get(0)
            return 0, zan_count
        except Exception, e:
            debug.get_debug_detail(e)
            transaction.rollback()
            return 99900, dict_err.get(99900)

    @transaction.commit_manually
    def cancel_zan(self, user_id, service_id):
        try:
            assert all([user_id, service_id])
        except:
            transaction.rollback()
            return 99800, dict_err.get(99800)

        if not Zan.objects.filter(user_id=user_id, service=service_id):
            transaction.rollback()
            return 99601, dict_err.get(99601)

        try:
            Zan.objects.filter(user_id=user_id, service=service_id).delete()
            ServiceBase().minus_zan_count(service_id)
            zan_count = ServiceBase().get_service_by_id(service_id).zan_count
            transaction.commit()
            # return 0, dict_err.get(0)
            return 0, zan_count
        except Exception, e:
            debug.get_debug_detail(e)
            transaction.rollback()
            return 99900, dict_err.get(99900)

    def get_zan_by_user_id(self, user_id):
        return Zan.objects.select_related("Service").filter(user_id=user_id)

    def is_zan(self, service_id, user_id):
        if not (service_id and user_id):
            return 99800, dict_err.get(99800)

        return Zan.objects.filter(service_id=service_id, user_id=user_id).count() > 0


class KindOpenInfoBase(object):

    def __init__(self):
        pass

    def __del__(self):
        pass

    def get_info_by_id(self, info_id):
        try:
            return KindOpenInfo.objects.get(id=info_id)
        except KindOpenInfo.DoesNotExist:
            return None

    def search_infos_for_admin(self, name, city_name=''):
        objs = KindOpenInfo.objects.all()

        if name:
            objs = objs.filter(kind__name__icontains=name)

        if city_name:
            from city.interface import CityBase
            city = CityBase().get_city_by_name(city_name)

            if city:
                objs = objs.filter(city_id=city.id)

        return objs

    def add_info(self, kind, city_id, open_time):
        if not (kind and city_id and open_time):
            return 99800, dict_err.get(99800)

        try:
            obj = KindOpenInfo.objects.create(
                kind_id=kind,
                city_id=city_id,
                open_time=open_time
            )
        except Exception, e:
            debug.get_debug_detail(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def remove_info(self, info_id):

        if not info_id:
            return 99800, dict_err.get(99800)

        KindOpenInfo.objects.filter(id=info_id).delete()

        return 0, dict_err.get(0)


class OrderBase(object):

    def create_order(self, user_id, service_id, product_id=None, price=0):

        if not (user_id and service_id):
            return 99800, dict_err.get(99800)

        service = ServiceBase().get_service_by_id(service_id)
        if not service:
            return 20103, dict_err.get(20103)

        # 是否已经预约中
        if Order.objects.filter(
            state__in=(0, 1),
            user_id=user_id,
            service_id=service_id
        ).count() > 0:
            return 20301, dict_err.get(20301)

        try:
            obj = Order.objects.create(
                user_id=user_id,
                service_id=service_id,
                product_id=product_id,
                price=price
            )
        except Exception, e:
            debug.get_debug_detail(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def get_order_by_id(self, order_id):
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None

    def get_order_by_user_id(self, user_id):
        return Order.objects.select_related("service").filter(user_id=user_id)

    def search_orders_for_admin(self, name, service_name="", state=None):
        objs = Order.objects.all()

        if state:
            objs = objs.filter(state=state)

        if service_name:
            objs = objs.filter(service__name__icontains=service_name)

        return objs

    def modify_order(self, obj_id, state=0, sort=0):

        if not (obj_id):
            return 99800, dict_err.get(99800)

        obj = self.get_order_by_id(obj_id)
        if not obj:
            return 20201, dict_err.get(20201)

        try:
            obj.sort = sort
            obj.state = state
            obj.save()
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)
