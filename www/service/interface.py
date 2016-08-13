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
            kinds = Kind.objects.filter(kind_type=kt[0])
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

        product = Product.objects.create(name=name, service_id=service_id, des=des, price=price, cover=cover, summary=summary)

        return 0, product

    def get_products_by_service(self, service):
        return Product.objects.select_related("service").filter(service=service)

    def get_product_by_id(self, product_id):
        try:
            return Product.objects.select_related("service").get(id=product_id)
        except Service.DoesNotExist:
            return None


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
            transaction.commit()
            return 0, zan
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
            transaction.commit()
            return 0, dict_err.get(0)
        except Exception, e:
            debug.get_debug_detail(e)
            transaction.rollback()
            return 99900, dict_err.get(99900)

    def get_zan_by_user_id(self, user_id):
        return Zan.objects.select_related("Service").filter(user_id=user_id)
