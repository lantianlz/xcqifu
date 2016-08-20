# -*- coding: utf-8 -*-

import json
import urllib
import datetime
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required

from www.account.interface import UserBase
from www.service.interface import KindOpenInfoBase
from www.city.interface import CityBase

@verify_permission('')
def kind_open_info(request, template_name='pc/admin/kind_open_info.html'):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_info(objs, num):
    data = []

    for x in objs:
        num += 1

        city = CityBase().get_city_by_id(x.city_id)

        data.append({
            'num': num,
            'id': x.id,
            'kind_name': x.kind.name,
            'city_name': city.city if city else '',
            'open_time': str(x.open_time)
        })

    return data


@verify_permission('query_kind_open_info')
def search(request):
    data = []

    name = request.REQUEST.get('name')
    city = request.REQUEST.get('city')
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = KindOpenInfoBase().search_infos_for_admin(name, city)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_info(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_kind_open_info')
def get_info_by_id(request):
    info_id = request.REQUEST.get('info_id')

    data = format_info([KindOpenInfoBase().get_info_by_id(info_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('add_kind_open_info')
@common_ajax_response
def add_info(request):
    kind = request.POST.get('kind')
    city = request.POST.get('city')
    open_time = request.POST.get('open_time')

    flag, msg = KindOpenInfoBase().add_info(kind, city, open_time)

    return flag, msg.id if flag == 0 else msg


@verify_permission('remove_kind_open_info')
@common_ajax_response
def remove_info(request):
    info_id = request.POST.get('info_id')
    print info_id
    return KindOpenInfoBase().remove_info(info_id)







