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
from www.service.interface import ProductBase

@verify_permission('')
def verify_info(request, template_name='pc/admin/verify_info.html'):
    from www.service.models import Product
    all_states = [
        {'name': u'全部', 'value': -1},
        {'name': u'已认证', 'value': 1}, 
        {'name': u'未认证', 'value': 0}, 
    ]
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_info(objs, num):
    data = []

    for x in objs:
        num += 1

        user = UserBase().get_user_by_id(x.user_id)

        data.append({
            'num': num,
            'id': x.id,
            'user_name': user.nick if user else '',
            'user_id': x.user_id,
            'user_avatar': user.get_avatar_65() if user else '',
            'name': x.name,
            'mobile': x.mobile,
            'title': x.title,
            'company_name': x.company_name,
            'company_short_name': x.company_short_name,
            'state': x.state,
            'create_time': str(x.create_time),
            'update_time': str(x.update_time)
        })

    return data


@verify_permission('query_verify_user')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    state = request.REQUEST.get('state')
    state = {'-1': None, '1': 1, '0': 0}[state]
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = VerifyInfoBase().search_infos_for_admin(name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_info(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_verify_user')
def get_info_by_id(request):
    info_id = request.REQUEST.get('info_id')

    data = format_info([VerifyInfoBase().get_info_by_id(info_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_verify_user')
@common_ajax_response
def modify_info(request):
    obj_id = request.POST.get('obj_id')
    name = request.POST.get('name')
    mobile = request.POST.get('mobile')
    title = request.POST.get('title')
    company_name = request.POST.get('company_name')
    company_short_name = request.POST.get('company_short_name')
    state = request.POST.get('state')
    
    return VerifyInfoBase().modify_info(
        obj_id, name, mobile, title, company_name, company_short_name, state
    )


