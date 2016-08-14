# -*- coding: utf-8 -*-

import json
import urllib
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required

from www.account.interface import UserBase
from www.service.interface import KindBase

@verify_permission('')
def kind(request, template_name='pc/admin/kind.html'):
    from www.service.models import Kind
    kind_type_choices = [{'name': x[1], 'value': x[0]} for x in Kind.kind_type_choices]
    all_states = [
        {'name': u'全部', 'value': -1},
        {'name': u'有效', 'value': 1}, 
        {'name': u'无效', 'value': 0}, 
    ]
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_kind(objs, num):
    data = []

    for x in objs:
        num += 1

        data.append({
            'num': num,
            'id': x.id,
            'name': x.name,
            'slogan': x.slogan,
            'kind_type': x.kind_type,
            'kind_type_str': x.get_kind_type_display(),
            'hot': x.hot,
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

    objs = KindBase().search_kinds_for_admin(name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_kind(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_kind')
def get_kind_by_id(request):
    kind_id = request.REQUEST.get('kind_id')

    data = format_kind([KindBase().get_kind_by_id(kind_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_kind')
@common_ajax_response
def modify_kind(request):
    obj_id = request.POST.get('obj_id')
    name = request.POST.get('name')
    kind_type = request.POST.get('kind_type')
    hot = request.POST.get('hot')
    sort = request.POST.get('sort')
    state = request.POST.get('state')
    slogan = request.POST.get('slogan')
    
    return KindBase().modify_kind(
        obj_id, name, kind_type, hot, sort, state, slogan
    )

@verify_permission('add_kind')
@common_ajax_response
def add_kind(request):
    name = request.POST.get('name')
    kind_type = request.POST.get('kind_type')
    hot = request.POST.get('hot')
    sort = request.POST.get('sort')
    state = request.POST.get('state')
    slogan = request.POST.get('slogan')

    flag, msg = KindBase().add_kind(
        name, kind_type, hot, sort, state, slogan
    )

    return flag, msg.id if flag == 0 else msg


@member_required
def get_kinds_by_name(request):
    '''
    根据名字查询类别
    '''
    name = request.REQUEST.get('name')

    result = []

    objs = KindBase().get_kinds_by_name(name)

    if objs:
        for x in objs:
            result.append([x.id, x.name, None, x.name])

    return HttpResponse(json.dumps(result), mimetype='application/json')

