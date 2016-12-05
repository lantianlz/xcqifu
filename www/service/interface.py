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

from www.account.interface import UserBase, ExternalTokenBase
from www.service.models import Kind, KindOpenInfo, Service, Product, \
Order, Zan, Company, CompanyManager, CashAccount, CashRecord, \
ServiceCashAccount, ServiceCashRecord, OrderRecord

DEFAULT_DB = 'default'

dict_err = {
    20101: u'该类别下已有同名供应商',
    20102: u'赞一次就可以了，多了会骄傲',
    20103: u'没有找到对应的供应商',

    20201: u'没有找到对应的产品',
    20202: u'已存在同名的产品',

    20301: u'已预约，客服人员将在24小时内联系你',
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

    def search_products_for_admin(self, name, service_name, state):
        objs = self.get_all_products(state)

        if name:
            objs = objs.filter(name__icontains=name)

        if service_name:
            objs = objs.filter(service__name__icontains=service_name)

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
        from www.tasks import async_send_new_order_template_msg
        from www.weixin.weixin_config import staff_open_ids
        from www.account.interface import VerifyInfoBase

        if not (user_id and service_id):
            return 99800, dict_err.get(99800)

        service = ServiceBase().get_service_by_id(service_id)
        if not service:
            return 20103, dict_err.get(20103)

        # 是否已经预约中
        if Order.objects.filter(state__in=(0, 1), user_id=user_id, service_id=service_id).count() > 0:
            return 20301, dict_err.get(20301)

        try:
            obj = Order.objects.create(user_id=user_id, service_id=service_id, product_id=product_id, price=price)
            ServiceBase().add_order_count(service_id)  # 预约次数加一

            # 发送模板通知
            for openid in staff_open_ids:
                verfiy_info = VerifyInfoBase().get_info_by_user_id(user_id)
                if verfiy_info:
                    create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    async_send_new_order_template_msg.delay(openid=openid, name=verfiy_info.name, mobile=verfiy_info.mobile,
                                                            create_time=create_time, service_name=service.name)
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
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


class CompanyBase(object):

    def get_all_company(self, state=None):
        objs = Company.objects.all()

        if state != None:
            objs = objs.filter(state=state)

        return objs

    def search_companys_for_admin(self, name, short_name):
        objs = self.get_all_company()

        if name:
            objs = objs.filter(name__contains=name)

        if short_name:
            objs = objs.filter(short_name__contains=short_name)

        return objs

    def get_company_by_id(self, id):
        try:
            ps = dict(id=id)

            return Company.objects.get(**ps)
        except Company.DoesNotExist:
            return ""

    def add_company(self, name, staff_name, mobile, tel, addr, city_id, \
        sort, des, person_count, logo, short_name):

        if not (name and staff_name and mobile and addr and city_id):
            return 99800, dict_err.get(99800)

        if Company.objects.filter(name=name):
            return 20201, dict_err.get(20201)

        try:
            obj = Company.objects.create(
                name=name,
                staff_name=staff_name,
                mobile=mobile,
                tel=tel,
                addr=addr,
                city_id=city_id,
                sort=sort,
                des=des,
                person_count=person_count,
                logo=logo,
                short_name=short_name
            )

            # 创建公司对应的账户
            CashAccount.objects.create(company=obj)

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def modify_company(self, company_id, name, staff_name, mobile, tel, \
        addr, city_id, sort, des, state, person_count, logo, short_name):
        if not (name and staff_name and mobile and addr and city_id):
            return 99800, dict_err.get(99800)

        obj = self.get_company_by_id(company_id)
        if not obj:
            return 20202, dict_err.get(20202)

        if obj.name != name and Company.objects.filter(name=name):
            return 20201, dict_err.get(20201)

        try:
            obj.name = name
            obj.staff_name = staff_name
            obj.mobile = mobile
            obj.tel = tel
            obj.addr = addr
            obj.city_id = city_id
            obj.sort = sort
            obj.des = des
            obj.state = state
            obj.person_count = person_count
            obj.logo = logo 
            obj.short_name = short_name
            obj.save()
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def get_companys_by_name(self, name=""):
        objs = self.get_all_company()

        if name:
            objs = objs.filter(name__contains=name)

        return objs[:10]


class CompanyManagerBase(object):

    def get_cm_by_user_id(self, user_id):
        """
        @note: 获取用户管理的第一个公司，用于自动跳转到管理的公司
        """
        cms = list(CompanyManager.objects.select_related("company").filter(user_id=user_id))
        if cms:
            return cms[0]

    def check_user_is_cm(self, company_id, user):
        """
        @note: 判断用户是否是某个公司管理员
        """

        try:
            if isinstance(user, (str, unicode)):
                user = UserBase().get_user_by_id(user)

            cm = CompanyManager.objects.filter(company__id=company_id, user_id=user.id)

            return True if (cm or user.is_staff()) else False
        except Exception, e:
            return False

    def add_company_manager(self, company_id, user_id):
        if not (company_id and user_id):
            return 99800, dict_err.get(99800)

        if user_id and not UserBase().get_user_login_by_id(user_id):
            return 99600, dict_err.get(99600)

        if CompanyManager.objects.filter(user_id=user_id, company__id=company_id):
            return 20601, dict_err.get(20601)

        try:
            cm = CompanyManager.objects.create(user_id=user_id, company_id=company_id)
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, cm

    def search_managers_for_admin(self, company_name):
        objs = CompanyManager.objects.select_related("company").all()

        if company_name:
            objs = objs.filter(company__name__contains=company_name)

        return objs

    def get_manager_by_id(self, manager_id):
        try:
            return CompanyManager.objects.select_related("company").get(id=manager_id)
        except CompanyManager.DoesNotExist:
            return ''

    def delete_company_manager(self, manager_id):
        if not manager_id:
            return 99800, dict_err.get(99800)

        try:
            CompanyManager.objects.get(id=manager_id).delete()
        except Exception:
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def get_managers_by_company(self, company_id):
        return CompanyManager.objects.filter(company_id = company_id)


class CashAccountBase(object):

    '''
    公司现金账户
    '''

    def get_all_accounts(self):
        return CashAccount.objects.all()

    def get_accounts_for_admin(self, name):
        objs = self.get_all_accounts()

        if name:
            objs = objs.select_related('company').filter(company__name__contains=name)

        return objs, objs.filter(balance__lt=0).aggregate(Sum('balance'))['balance__sum'] or 0

    def get_cash_account_by_id(self, account_id):
        try:
            return CashAccount.objects.select_related("company").get(id=account_id)
        except CashAccount.DoesNotExist:
            return ''

    def modify_cash_account(self, account_id, max_overdraft):

        obj = self.get_cash_account_by_id(account_id)
        if not obj:
            return 20701, dict_err.get(20701)

        try:
            obj.max_overdraft = max_overdraft
            obj.save()
        except Exception:
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def get_account_by_company(self, company_id):
        try:
            return CashAccount.objects.get(company_id=company_id)
        except CashAccount.DoesNotExist:
            return ''


class CashRecordBase(object):

    def send_balance_insufficient_notice(self, company, balance, max_overdraft):
        # 发送邮件提醒
        from www.tasks import async_send_email
        title = u'账户已达最高透支额'
        content = u'账户「%s」当前余额「%.2f」元，已达「%.2f」元最高透支额，请联系充值' % (company.name, balance, max_overdraft)
        async_send_email("vip@3-10.cc", title, content)

        # 发送微信提醒
        from weixin.interface import WeixinBase
        for manager in CompanyManagerBase().get_managers_by_company(company.id):
            
            to_user_openid = ExternalTokenBase().get_weixin_openid_by_user_id(manager.user_id)

            if to_user_openid:
                WeixinBase().send_balance_insufficient_template_msg(
                    to_user_openid, u"账户已达「%.2f」元最高透支额，请联系充值" % max_overdraft, 
                    company.name, u"%.2f 元" % balance, 
                    u"感谢您的支持，祝工作愉快"
                )

    def send_recharge_success_notice(self, company, amount, balance, pay_type=1):

        PAY_TYPE_DICT = {1: u'人工转账', 2: u'支付宝在线支付'}
        pay_type_str = PAY_TYPE_DICT.get(pay_type, u'人工转账')

        # 发送邮件提醒
        from www.tasks import async_send_email
        title = u'账户充值成功'
        content = u'账户「%s」通过「%s」成功充值「%.2f」元，当前余额「%.2f」元。' % (company.name, pay_type_str, amount, balance)
        async_send_email("vip@3-10.cc", title, content)

        # 发送微信提醒
        from weixin.interface import WeixinBase
        for manager in CompanyManagerBase().get_managers_by_company(company.id):
            
            to_user_openid = ExternalTokenBase().get_weixin_openid_by_user_id(manager.user_id)

            if to_user_openid:
                WeixinBase().send_recharge_success_template_msg(
                    to_user_openid, 
                    u"%s，您已成功充值" % company.name,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                    u"%.2f 元" % amount, 
                    u"账户余额：%.2f 元" % balance
                )

    def get_all_records(self, operation=None, is_invoice=None):
        objs = CashRecord.objects.all()
        if operation:
            objs = objs.filter(operation=operation)
        if is_invoice:
            objs = objs.filter(is_invoice=is_invoice)

        return objs

    def get_records_for_admin(self, start_date, end_date, name, operation=None, is_invoice=None, is_alipay=False):
        objs = self.get_all_records(operation, is_invoice).filter(create_time__range=(start_date, end_date))

        if name:
            objs = objs.filter(cash_account__company__name__contains=name)

        if operation == None and is_alipay:
            objs = objs.filter(operation=0, notes=u'支付宝在线充值')

        all_sum = 0
        # 如果没有指定操作类型
        if not operation:
            in_sum = objs.filter(operation=0).aggregate(Sum('value'))['value__sum']
            in_sum = in_sum or 0
            out_sum = objs.filter(operation=1).aggregate(Sum('value'))['value__sum']
            out_sum = out_sum or 0
            all_sum = in_sum - out_sum
        else:
            all_sum = objs.aggregate(Sum('value'))['value__sum']
            all_sum = all_sum or 0

        return objs, all_sum

    def validate_record_info(self, company_id, value, operation, notes):
        value = float(value)
        operation = int(operation)
        company = CompanyBase().get_company_by_id(company_id)
        assert operation in (0, 1)
        assert value > 0 and notes and company

    @transaction.commit_manually(using=DEFAULT_DB)
    def add_cash_record_with_transaction(self, company_id, value, operation, notes, ip=None, is_invoice=1, pay_type=1):
        try:
            errcode, errmsg = self.add_cash_record(company_id, value, operation, notes, ip, is_invoice, pay_type)
            if errcode == 0:
                transaction.commit(using=DEFAULT_DB)
            else:
                transaction.rollback(using=DEFAULT_DB)
            return errcode, errmsg
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            transaction.rollback(using=DEFAULT_DB)
            return 99900, dict_err.get(99900)

    def add_cash_record(self, company_id, value, operation, notes, ip=None, is_invoice=1, pay_type=1):
        try:
            try:
                value = decimal.Decimal(value)
                operation = int(operation)
                self.validate_record_info(company_id, value, operation, notes)
            except Exception, e:
                return 99801, dict_err.get(99801)

            account, created = CashAccount.objects.get_or_create(company_id=company_id)

            if operation == 0:
                account.balance += value
            elif operation == 1:
                account.balance -= value
            account.save()

            CashRecord.objects.create(
                cash_account=account,
                value=value,
                current_balance=account.balance,
                operation=operation,
                notes=notes,
                ip=ip,
                is_invoice=is_invoice
            )

            # 转出时判断是否超过透支额  发送提醒
            if operation == 1 and account.balance < 0 and abs(account.balance) >= account.max_overdraft:
                self.send_balance_insufficient_notice(
                    account.company, 
                    account.balance, 
                    account.max_overdraft
                )

            # 转入发送提醒
            if operation == 0:
                self.send_recharge_success_notice(
                    account.company,
                    value,
                    account.balance,
                    pay_type
                )

            return 0, dict_err.get(0)
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)


    def get_records_by_company(self, company_id, start_date, end_date):
        objs = self.get_all_records().filter(
            cash_account__company__id = company_id,
            create_time__range=(start_date, end_date)
        )

        return objs

    def get_records_group_by_company(self, start_date, end_date, operation=None, is_invoice=None):
        '''
        根据公司分组获取现金流水记录

        '''
        objs = CashRecord.objects.filter(
            create_time__range=(start_date, end_date)
        )
        if operation is not None:
            objs = objs.filter(operation=operation)

        if is_invoice is not None:
            objs = objs.filter(is_invoice=is_invoice)

        return objs.values('cash_account__company_id').annotate(recharge=Sum('value'))

    def change_is_invoice(self, record_id):
        try:
            obj = CashRecord.objects.get(id = record_id)
            if obj.is_invoice == 1:
                obj.is_invoice = 0
            else:
                obj.is_invoice = 1

            obj.save()
            return 0, obj.is_invoice

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)


class ServiceCashAccountBase(object):

    def get_all_accounts(self):
        return ServiceCashAccount.objects.all()

    def get_accounts_for_admin(self, name):
        objs = self.get_all_accounts()

        if name:
            objs = objs.select_related('service').filter(service__name__contains=name)

        return objs

    def get_service_cash_account_by_id(self, account_id):
        try:
            return ServiceCashAccount.objects.select_related("service").get(id=account_id)
        except ServiceCashAccount.DoesNotExist:
            return ''

    def get_account_by_service(self, service_id):
        try:
            return ServiceCashAccount.objects.get(service_id=service_id)
        except ServiceCashAccount.DoesNotExist:
            return ''


class ServiceCashRecordBase(object):

    def get_all_records(self, operation=None):
        objs = ServiceCashRecord.objects.all()
        if operation:
            objs = objs.filter(operation=operation)

        return objs

    def get_records_for_admin(self, start_date, end_date, name, operation=None):
        objs = self.get_all_records(operation).filter(create_time__range=(start_date, end_date))

        if name:
            objs = objs.filter(cash_account__service__name__contains=name)

        all_sum = 0
        # 如果没有指定操作类型
        if not operation:
            in_sum = objs.filter(operation=0).aggregate(Sum('value'))['value__sum']
            in_sum = in_sum or 0
            out_sum = objs.filter(operation=1).aggregate(Sum('value'))['value__sum']
            out_sum = out_sum or 0
            all_sum = in_sum - out_sum
        else:
            all_sum = objs.aggregate(Sum('value'))['value__sum']
            all_sum = all_sum or 0

        return objs, all_sum

    def validate_record_info(self, service_id, value, operation, notes):
        value = float(value)
        operation = int(operation)
        service = ServiceBase().get_service_by_id(service_id)
        assert operation in (0, 1)
        assert value > 0 and notes and service

    @transaction.commit_manually(using=DEFAULT_DB)
    def add_cash_record_with_transaction(self, service_id, value, operation, notes, ip=None, order_id=None):
        try:
            errcode, errmsg = self.add_cash_record(service_id, value, operation, notes, ip, order_id)
            if errcode == 0:
                transaction.commit(using=DEFAULT_DB)
            else:
                transaction.rollback(using=DEFAULT_DB)
            return errcode, errmsg
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            transaction.rollback(using=DEFAULT_DB)
            return 99900, dict_err.get(99900)

    def add_cash_record(self, service_id, value, operation, notes, ip=None, order_id=None):
        try:
            try:
                value = decimal.Decimal(value)
                operation = int(operation)
                self.validate_record_info(service_id, value, operation, notes)
            except Exception, e:
                return 99801, dict_err.get(99801)

            account, created = ServiceCashAccount.objects.get_or_create(service_id=service_id)

            if operation == 0:
                account.balance += value
            elif operation == 1:
                account.balance -= value
            account.save()

            ServiceCashRecord.objects.create(
                cash_account=account,
                value=value,
                current_balance=account.balance,
                operation=operation,
                notes=notes,
                ip=ip,
                order_id=order_id
            )

            return 0, dict_err.get(0)
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)


class OrderRecordBase(object):

    def generate_order_no(self, pr):
        """
        @note: 生成订单的id，传入不同前缀来区分订单类型
        """
        postfix = '%s' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # 纯数字
        if pr:
            postfix = '%s%s%02d' % (pr, postfix, random.randint(0, 99))
        return postfix

    def search_records_for_admin(self, company_name, service_name, salesperson_name, state=None):
        objs = OrderRecord.objects.all()

        if state:
            objs = objs.filter(state = state)

        if company_name:
            objs.filter(company__name__icontains=company_name)

        if service_name:
            objs.filter(service__name__icontains=service_name)

        if salesperson_name:
            user = UserBase().get_user_by_nick(salesperson_name)
            if user:
                objs.filter(salesperson=user.id)

        return objs

    def get_record_by_id(self, record_id):
        try:
            return OrderRecord.objects.get(id=record_id)
        except OrderRecord.DoesNotExist:
            return ''

    def add_record(self, company_id, product, service_id, salesperson, price, 
        amount, total_price, settlement_price, gross_profit_rate, tax_rate, percentage_rate,
        distribution_time, state=1, is_test=False, notes=''):

        if not (company_id and product and service_id and salesperson and price 
            and amount and total_price and settlement_price and gross_profit_rate 
            and tax_rate and percentage_rate and distribution_time):
            return 99800, dict_err.get(99800)

        try:
            obj = OrderRecord.objects.create(
                order_no=self.generate_order_no("T"),
                company_id = company_id,
                product = product,
                service_id = service_id,
                salesperson = salesperson,
                price = price,
                amount = amount,
                total_price = total_price,
                settlement_price = settlement_price,
                gross_profit_rate = gross_profit_rate,
                tax_rate = tax_rate,
                percentage_rate = percentage_rate,
                state = state,
                is_test = is_test,
                notes = notes,
                distribution_time = distribution_time
            )
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

        return 0, obj

    def modify_record(self, record_id, product, price, 
        amount, total_price, settlement_price, gross_profit_rate, tax_rate, percentage_rate,
        distribution_time, is_test=False, notes=''):

        if not (record_id and product and price 
            and amount and total_price and settlement_price and gross_profit_rate 
            and tax_rate and percentage_rate and distribution_time):
            return 99800, dict_err.get(99800)

        obj = self.get_record_by_id(record_id)
        if not obj:
            return 99800, dict_err.get(99800)

        try:
            obj.product = product
            obj.price = price
            obj.amount = amount
            obj.total_price = total_price
            obj.settlement_price = settlement_price
            obj.gross_profit_rate = gross_profit_rate
            obj.tax_rate = tax_rate
            obj.percentage_rate = percentage_rate
            obj.distribution_time = distribution_time
            obj.is_test = is_test
            obj.notes = notes
            obj.save()
            return 0, dict_err.get(0)

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)

    @transaction.commit_manually(using=DEFAULT_DB)
    def confirm_record(self, record_id, ip):
        if not record_id:
            return 99800, dict_err.get(99800)

        obj = self.get_record_by_id(record_id)
        if not obj:
            transaction.rollback(using=DEFAULT_DB)
            return 99800, dict_err.get(99800)

        try:
            obj.state = 1
            obj.confirm_time = datetime.datetime.now()
            obj.save()

            # 试吃订单不操作账户
            if obj.is_test:
                transaction.commit(using=DEFAULT_DB)
            else:
                # 操作公司现金账户
                company_code, msg = CashRecordBase().add_cash_record(
                    obj.company_id,
                    obj.total_price,
                    1,
                    u"订单「%s」确认" % obj.order_no,
                    ip
                )
                if company_code != 0:
                    transaction.rollback(using=DEFAULT_DB)
                    return company_code, dict_err.get(company_code)

                # 操作服务商现金账户
                service_code, msg = ServiceCashRecordBase().add_cash_record(
                    obj.service_id, 
                    obj.settlement_price, 
                    0, 
                    u"订单「%s」确认" % obj.order_no, 
                    ip, 
                    obj.id
                )
                if service_code != 0:
                    transaction.rollback(using=DEFAULT_DB)
                    return service_code, dict_err.get(service_code)

                transaction.commit(using=DEFAULT_DB)
            return 0, dict_err.get(0)

        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            transaction.rollback(using=DEFAULT_DB)
            return 99900, dict_err.get(99900)

    def drop_record(self, record_id):
        if not record_id:
            return 99800, dict_err.get(99800)

        obj = self.get_record_by_id(record_id)
        if not obj:
            return 99800, dict_err.get(99800)

        try:
            obj.state = 2
            obj.save()
            return 0, dict_err.get(0)
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
            return 99900, dict_err.get(99900)










