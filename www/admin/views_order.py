# -*- coding: utf-8 -*-

import json
import urllib
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings

from common import utils, page
from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required
from www.misc import qiniu_client

from www.account.interface import UserBase, VerifyInfoBase
from www.service.interface import ProductBase, OrderBase

@verify_permission('')
def order(request, template_name='pc/admin/order.html'):
    from www.service.models import Order
    state_choices = [{'name': x[1], 'value': x[0]} for x in Order.state_choices]
    all_state_choices = [{'name': x[1], 'value': x[0]} for x in Order.state_choices]
    all_state_choices.insert(0, {'name': u'全部', 'value': -1})
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_order(objs, num):
    data = []

    for x in objs:
        num += 1

        info = VerifyInfoBase().get_info_by_user_id(x.user_id)

        data.append({
            'num': num,
            'id': x.id,
            'user_name': info.name if info else '',
            'user_title': info.title if info else '',
            'user_mobile': info.mobile if info else '',
            'company_name': info.company_name if info else '',
            'service_name': x.service.name,
            'product_name': x.product.name if x.product else '',
            'price': str(x.price),
            'state': x.state,
            'sort': x.sort,
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_order')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    service_name = request.REQUEST.get('service_name')
    state = request.REQUEST.get('state')
    state = None if state == "-1" else state
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = OrderBase().search_orders_for_admin(name, service_name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_order(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_order')
def get_order_by_id(request):
    order_id = request.REQUEST.get('order_id')

    data = format_order([OrderBase().get_order_by_id(order_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_order')
@common_ajax_response
def modify_order(request):
    obj_id = request.POST.get('obj_id')
    sort = request.POST.get('sort')
    state = request.POST.get('state')
    
    return OrderBase().modify_order(
        obj_id, state, sort
    )


