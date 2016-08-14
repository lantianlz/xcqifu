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
from www.city.interface import CityBase
from www.service.interface import KindBase, ServiceBase

@verify_permission('')
def service(request, template_name='pc/admin/service.html'):
    from www.service.models import Service
    level_choices = [{'name': x[1], 'value': x[0]} for x in Service.level_choices]
    all_states = [
        {'name': u'全部', 'value': -1},
        {'name': u'有效', 'value': 1}, 
        {'name': u'无效', 'value': 0},
    ]
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_service(objs, num):
    data = []

    for x in objs:
        num += 1

        city = CityBase().get_city_by_id(x.city_id)
        user = UserBase().get_user_by_id(x.recommend_user_id) if x.recommend_user_id else ''

        data.append({
            'num': num,
            'id': x.id,
            'name': x.name,
            'kind_id': x.kind_id,
            'kind_name': x.kind.name,
            'logo': x.logo,
            'city_id': x.city_id,
            'city_name': city.city if city else '',
            'summary': x.summary,
            'des': x.des,
            'imgs': x.imgs,
            'service_area': x.service_area,
            'tel': x.tel,
            'addr': x.addr,
            'longitude': x.longitude,
            'latitude': x.latitude,
            'join_time': str(x.join_time),
            'recommend_user_id': user.id if user else '',
            'recommend_user_nick': user.nick if user else '',
            'recommend_des': x.recommend_des,
            'zan_count': x.zan_count,
            'order_count': x.order_count,
            'level': x.level,
            'level_str': x.get_level_display(),
            'is_show': x.is_show,
            'state': x.state,
            'sort': x.sort,
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_kind')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    state = request.REQUEST.get('state')
    state = {'-1': None, '1': True, '0': False}[state]
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = ServiceBase().search_services_for_admin(name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_service(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_kind')
def get_service_by_id(request):
    service_id = request.REQUEST.get('service_id')

    data = format_service([ServiceBase().get_service_by_id(service_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_kind')
@common_ajax_response
def modify_service(request):
    obj_id = request.POST.get('obj_id')
    name = request.POST.get('name')
    kind = request.POST.get('kind')
    city = request.POST.get('city')
    summary = request.POST.get('summary')
    des = request.POST.get('des')
    imgs = request.POST.get('imgs')
    service_area = request.POST.get('service_area')
    tel = request.POST.get('tel')
    addr = request.POST.get('addr')
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')
    join_time = request.POST.get('join_time')
    recommend_user_id = request.POST.get('recommend_user_id')
    recommend_des = request.POST.get('recommend_des')
    zan_count = request.POST.get('zan_count')
    order_count = request.POST.get('order_count')
    level = request.POST.get('level')
    is_show = request.POST.get('is_show')
    state = request.POST.get('state')
    sort = request.POST.get('sort')

    obj = ServiceBase().get_service_by_id(obj_id)
    logo_name = obj.logo

    logo = request.FILES.get('logo')
    if logo:
        flag, logo_name = qiniu_client.upload_img(logo, img_type='service')
        logo_name = '%s/%s' % (settings.IMG0_DOMAIN, logo_name)
    
    flag, msg = ServiceBase().modify_service(
        obj_id, name, kind, logo_name, city, summary, des, imgs, service_area,
        tel, addr, longitude, latitude, join_time, recommend_user_id, 
        recommend_des, zan_count, order_count, level, is_show, state, sort
    )
    
    if flag == 0:
        url = "/admin/service?#modify/%s" % (obj.id)
    else:
        url = "/admin/service?%s#modify/%s" % (msg, obj.id)

    return HttpResponseRedirect(url)

@verify_permission('add_kind')
@common_ajax_response
def add_service(request):
    name = request.POST.get('name')
    kind = request.POST.get('kind')
    city = request.POST.get('city')
    summary = request.POST.get('summary')
    des = request.POST.get('des')
    imgs = request.POST.get('imgs')
    service_area = request.POST.get('service_area')
    tel = request.POST.get('tel')
    addr = request.POST.get('addr')
    longitude = request.POST.get('longitude')
    latitude = request.POST.get('latitude')
    join_time = request.POST.get('join_time')
    recommend_user_id = request.POST.get('recommend_user_id')
    recommend_des = request.POST.get('recommend_des')
    zan_count = request.POST.get('zan_count')
    order_count = request.POST.get('order_count')
    level = request.POST.get('level')
    is_show = request.POST.get('is_show')
    state = request.POST.get('state')
    sort = request.POST.get('sort')

    logo_name = ''
    logo = request.FILES.get('logo')
    if logo:
        flag, logo_name = qiniu_client.upload_img(logo, img_type='service')
        logo_name = '%s/%s' % (settings.IMG0_DOMAIN, logo_name)
    
    flag, msg = ServiceBase().add_service(
        name, kind, logo_name, city, summary, des, imgs, service_area,
        tel, addr, longitude, latitude, join_time, recommend_user_id, 
        recommend_des, zan_count, order_count, level, is_show, state, sort
    )
    
    if flag == 0:
        url = "/admin/service?#modify/%s" % (msg.id)
    else:
        url = "/admin/service?%s" % (msg)

    return HttpResponseRedirect(url)