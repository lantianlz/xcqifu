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

from www.account.interface import UserBase, UserInviteBase
from www.service.interface import ProductBase

@verify_permission('')
def invite(request, template_name='pc/admin/invite.html'):
    from www.account.models import InviteQrcode
    state_choices = [{'name': x[1], 'value': x[0]} for x in InviteQrcode.state_choices]
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_invite(objs, num):
    data = []

    for x in objs:
        num += 1

        if x.qrcode.state == 0:
            user = UserBase().get_user_by_id(x.from_user_id)

        to_user = UserBase().get_user_by_id(x.to_user_id)

        data.append({
            'num': num,
            'id': x.id,
            'user_name': user.nick if user else x.qrcode.name,
            'user_id': user.id if user else '',
            'user_avatar': user.get_avatar_65() if user else '',
            'to_user_name': to_user.nick if to_user else '',
            'to_user_id': x.to_user_id,
            'to_user_avatar': to_user.get_avatar_65() if to_user else '',
            'to_user_des': to_user.des,
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_invite')
def search(request):
    data = []

    state = request.REQUEST.get('state')
    name = request.REQUEST.get('name')
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = UserInviteBase().search_invite_for_admin(int(state), name)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_invite(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )




