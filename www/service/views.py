# -*- coding: utf-8 -*-

import json
import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import common_ajax_response, member_required, request_limit_by_ip, auto_select_template

from www.account.interface import UserBase, VerifyInfoBase
from www.service.interface import KindBase, ServiceBase, ProductBase
from www.weixin.interface import WeixinBase, Sign


kb = KindBase()
sb = ServiceBase()


@auto_select_template
def index(request, template_name='mobile/index.html'):
    city_id = request.session.get("city_id", 1974)
    data = kb.get_kind_list(city_id=city_id)
    # print data

    # 转换成json
    data_json = json.dumps(data)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_list(request, kind_id, template_name='mobile/service/service_list.html'):

    kind = kb.get_kind_by_id(kind_id)

    _services = sb.get_service_by_kind(kind_id)
    services = []
    for i in range(_services.count()):
        temp = _services[i]
        setattr(temp, 'delays', 0.2 + i * 0.1)
        services.append(temp)

    last_delay = 0.2 + len(services) * 0.1

    # 如果服务商数量少于2显示 即将开放
    show_comingsoon = True if len(services) <= 2 else False

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_detail(request, service_id, template_name='mobile/service/service_detail.html'):
    service = sb.get_service_by_id(service_id)

    if not service:
        raise Http404

    if service.recommend_user_id:
        recommend_user = UserBase().get_user_by_id(service.recommend_user_id)
        recommend_user_info = dict(avatar=recommend_user.get_avatar_65, name=recommend_user.nick)
        verify_info = VerifyInfoBase().get_info_by_user_id(recommend_user.id)
        if verify_info:
            recommend_user_info.update(name=verify_info.name, title=verify_info.title, company_name=verify_info.company_name)
    products = ProductBase().get_products_by_service(service)

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def product_detail(request, product_id, template_name='mobile/service/product_detail.html'):
    product = ProductBase().get_product_by_id(product_id)

    if not product:
        raise Http404
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


@member_required
def my_order(request, template_name='mobile/service/my_order.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
