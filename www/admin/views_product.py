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

from www.account.interface import UserBase
from www.service.interface import ProductBase

@verify_permission('')
def product(request, template_name='pc/admin/product.html'):
    from www.service.models import Product
    all_states = [
        {'name': u'全部', 'value': -1},
        {'name': u'有效', 'value': 1}, 
        {'name': u'无效', 'value': 0}, 
    ]
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_product(objs, num):
    data = []

    for x in objs:
        num += 1

        data.append({
            'num': num,
            'id': x.id,
            'name': x.name,
            'service_id': x.service.id,
            'service_name': x.service.name,
            'cover': x.cover,
            'summary': x.summary,
            'des': x.des,
            'price': str(x.price),
            'params': x.params,
            'state': x.state,
            'sort': x.sort,
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_product')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    service_name = request.REQUEST.get('service_name')
    state = request.REQUEST.get('state')
    state = {'-1': None, '1': True, '0': False}[state]
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = ProductBase().search_products_for_admin(name, service_name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_product(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_product')
def get_product_by_id(request):
    product_id = request.REQUEST.get('product_id')

    data = format_product([ProductBase().get_product_by_id(product_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_kind')
@common_ajax_response
def modify_product(request):
    obj_id = request.POST.get('obj_id')
    name = request.POST.get('name')
    service = request.POST.get('service')
    summary = request.POST.get('summary')
    des = request.POST.get('des')
    price = request.POST.get('price')
    params = request.POST.get('params')
    state = request.POST.get('state')
    sort = request.POST.get('sort')

    obj = ProductBase().get_product_by_id(obj_id)
    cover_name = obj.cover

    cover = request.FILES.get('cover')
    if cover:
        flag, cover_name = qiniu_client.upload_img(cover, img_type='product')
        cover_name = '%s/%s' % (settings.IMG0_DOMAIN, cover_name)
    
    flag, msg = ProductBase().modify_product(
        obj_id, name, service, cover_name, summary, des, price, params, state, sort
    )
    
    if flag == 0:
        url = "/admin/product?#modify/%s" % (obj.id)
    else:
        url = "/admin/product?%s#modify/%s" % (msg, obj.id)

    return HttpResponseRedirect(url)


@verify_permission('add_product')
@common_ajax_response
def add_product(request):
    name = request.POST.get('name')
    service = request.POST.get('service')
    summary = request.POST.get('summary')
    des = request.POST.get('des')
    price = request.POST.get('price')
    params = request.POST.get('params')
    state = request.POST.get('state')
    sort = request.POST.get('sort')

    cover_name = ''
    cover = request.FILES.get('cover')
    if cover:
        flag, cover_name = qiniu_client.upload_img(cover, img_type='product')
        cover_name = '%s/%s' % (settings.IMG0_DOMAIN, cover_name)
    
    flag, msg = ProductBase().add_product(
        name, service, des, price, cover_name, summary
    )

    if flag == 0:
        url = "/admin/product?#modify/%s" % (msg.id)
    else:
        url = "/admin/product?%s" % (msg)

    return HttpResponseRedirect(url)
