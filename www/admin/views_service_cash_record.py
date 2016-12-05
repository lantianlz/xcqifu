# -*- coding: utf-8 -*-

import json, datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings

from www.misc.decorators import staff_required, common_ajax_response, verify_permission, log_sensitive_operation
from www.misc import qiniu_client
from common import utils, page

from www.service.interface import ServiceBase, ServiceCashRecordBase
from www.service.models import ServiceCashRecord

@verify_permission('')
def service_cash_record(request, template_name='pc/admin/service_cash_record.html'):
    operation_choices = [{'value': x[0], 'name': x[1]} for x in ServiceCashRecord.operation_choices]
    all_operations = [{'name': x[1], 'value': x[0]} for x in ServiceCashRecord.operation_choices]
    all_operations.insert(0, {'name': u'全部', 'value': -1})

    today = datetime.datetime.now()
    start_date= (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def format_record(objs, num):
    data = []

    for x in objs:
        num += 1

        service = ServiceBase().get_service_by_id(x.cash_account.service_id) if x.cash_account.service_id else None

        data.append({
            'num': num,
            'record_id': x.id,
            'balance': str(x.cash_account.balance),
            'service_id': service.id if service else '',
            'service_name': service.name if service else '',
            'value': str(x.value),
            'current_balance': str(x.current_balance),
            'operation': x.operation,
            'notes': x.notes,
            'ip': x.ip,
            'order_id': x.order_id or '',
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_service_cash_record')
def search(request):
    data = []

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)
    name = request.REQUEST.get('name')
    operation = request.REQUEST.get('operation')
    operation = None if operation == "-1" else operation
    
    page_index = int(request.REQUEST.get('page_index'))
    
    objs, sum_price = ServiceCashRecordBase().get_records_for_admin(start_date, end_date, name, operation)

    page_objs = page.Cpt(objs, count=10, page=page_index).info

    # 格式化json
    num = 10 * (page_index - 1)
    data = format_record(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'sum_price': str(sum_price or 0), 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )

@verify_permission('add_service_cash_record')
@log_sensitive_operation
@common_ajax_response
def add_service_cash_record(request):
    service_id = request.REQUEST.get('service_id')
    value = request.REQUEST.get('value')
    operation = request.REQUEST.get('operation')
    notes = request.REQUEST.get('notes')
    ip = utils.get_clientip(request)

    return ServiceCashRecordBase().add_cash_record_with_transaction(service_id, value, operation, notes, ip)

