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

from www.account.interface import UserBase, InviteQrcodeBase
from www.service.interface import ProductBase

@verify_permission('')
def channel_qrcode(request, template_name='pc/admin/channel_qrcode.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_channel_qrcode(objs, num):
    data = []

    for x in objs:
        num += 1


        data.append({
            'num': num,
            'id': x.id,
            'name': x.name,
            'unique_code': x.unique_code,
            'ticket': x.ticket,
            'user_count': x.user_count,
            'state': x.state,
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_channel_qrcode')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    is_sort = int(request.REQUEST.get('is_sort'))
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = InviteQrcodeBase().search_channel_qrcodes_for_admin(name, is_sort)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_channel_qrcode(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )

@verify_permission('query_channel_qrcode')
def get_code_by_id(request):
    code_id = request.REQUEST.get('code_id')

    data = format_channel_qrcode([InviteQrcodeBase().get_qrcode_by_id(code_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')

@verify_permission('modify_channel_qrcode')
@common_ajax_response
def modify_code(request):
    obj_id = request.POST.get('obj_id')
    name = request.POST.get('name')
    
    return InviteQrcodeBase().modify_qrcode(obj_id, name)

@verify_permission('add_channel_qrcode')
@common_ajax_response
def add_code(request):
    name = request.POST.get('name')

    flag, msg = InviteQrcodeBase().create_channel_qrcode(name)

    return flag, msg.id if flag == 0 else msg

