# -*- coding: utf-8 -*-

import json, datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings

from www.misc.decorators import staff_required, common_ajax_response, verify_permission, member_required
from www.misc import qiniu_client
from common import utils, page

from www.service.interface import ServiceBase, ServiceCashAccountBase

@verify_permission('')
def service_cash_account(request, template_name='pc/admin/service_cash_account.html'):
    today = datetime.datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    start_date = (today.replace(day=1)).strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def format_account(objs, num):
    data = []

    for x in objs:
        num += 1

        service = ServiceBase().get_service_by_id(x.service_id) if x.service_id else None

        data.append({
            'num': num,
            'account_id': x.id,
            'balance': str(x.balance),
            'service_id': service.id if service else '',
            'service_name': service.name if service else '',
        })

    return data


@verify_permission('query_service_cash_account')
def search(request):
    data = []

    service_name = request.REQUEST.get('service_name')
    
    page_index = int(request.REQUEST.get('page_index'))

    objs = ServiceCashAccountBase().get_accounts_for_admin(service_name)

    page_objs = page.Cpt(objs, count=10, page=page_index).info

    # 格式化json
    num = 10 * (page_index - 1)
    data = format_account(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_service_cash_account')
def get_cash_account_by_id(request):
    account_id = request.REQUEST.get('account_id')

    data = format_account([ServiceCashAccountBase().get_service_cash_account_by_id(account_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')
