# -*- coding: utf-8 -*-

import json
import datetime
import urllib
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required

from www.account.interface import UserBase
from www.service.interface import OrderRecordBase

@verify_permission('')
def order_record(request, template_name='pc/admin/order_record.html'):
    from www.service.models import OrderRecord
    state_choices = [{'name': x[1], 'value': x[0]} for x in OrderRecord.state_choices]
    all_state_choices = [{'name': x[1], 'value': x[0]} for x in OrderRecord.state_choices]
    all_state_choices.insert(0, {'name': u'全部', 'value': -1})

    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def format_record(objs, num):
    data = []

    for x in objs:
        num += 1

        salesperson = UserBase().get_user_by_id(x.salesperson)

        data.append({
            'num': num,
            'id': x.id,
            'company_id': x.company.id,
            'company_name': x.company.name,
            'product': x.product,
            'service_id': x.service.id,
            'service_name': x.service.name,
            'salesperson_id': salesperson.id if salesperson else '',
            'salesperson_name': salesperson.nick if salesperson else '',
            'price': str(x.smart_price()),
            'amount': x.amount,
            'total_price': str(x.smart_total_price()),
            'settlement_price': str(x.smart_settlement_price()),
            'gross_profit_rate': str(x.gross_profit_rate),
            'gross_profit': str(x.smart_gross_profit()),
            'tax_rate': str(x.tax_rate),
            'tax': str(x.smart_tax()),
            'net_rate': str(x.net_rate()),
            'net': str(x.smart_net()),
            'percentage': str(x.smart_percentage()),
            'percentage_rate': str(x.percentage_rate),
            'net_income_rate': str(x.net_income_rate()),
            'net_income': str(x.smart_net_income()),
            'state': x.state,
            'is_test': x.is_test,
            'notes': x.notes,
            'confirm_time': str(x.confirm_time) if x.confirm_time else '',
            'distribution_time': str(x.distribution_time)[:10],
            'create_time': str(x.create_time)
        })

    return data


@verify_permission('query_kind')
def search(request):
    data = []

    company_name = request.REQUEST.get('company_name')
    service_name = request.REQUEST.get('service_name')
    salesperson_name = request.REQUEST.get('salesperson_name')
    state = request.REQUEST.get('state')
    state = None if state == '-1' else state
    page_index = int(request.REQUEST.get('page_index'))
    per_count = 15

    objs = OrderRecordBase().search_records_for_admin(company_name, service_name, salesperson_name, state)

    page_objs = page.Cpt(objs, count=per_count, page=page_index).info

    # 格式化json
    num = per_count * (page_index - 1)
    data = format_record(page_objs[0], num)

    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


@verify_permission('query_kind')
def get_record_by_id(request):
    record_id = request.REQUEST.get('record_id')

    data = format_record([OrderRecordBase().get_record_by_id(record_id)], 1)[0]

    return HttpResponse(json.dumps(data), mimetype='application/json')


@verify_permission('modify_kind')
@common_ajax_response
def modify_record(request):
    obj_id = request.POST.get('obj_id')
    product = request.POST.get('product')
    price = request.POST.get('price')
    amount = request.POST.get('amount')
    total_price = request.POST.get('total_price')
    settlement_price = request.POST.get('settlement_price')
    gross_profit_rate = request.POST.get('gross_profit_rate')
    tax_rate = request.POST.get('tax_rate')
    percentage_rate = request.POST.get('percentage_rate')
    distribution_time = request.POST.get('distribution_time')
    is_test = request.POST.get('is_test')
    is_test = True if is_test == '1' else False
    notes = request.POST.get('notes')
    
    return OrderRecordBase().modify_record(
        obj_id, product, price, amount, total_price, settlement_price, 
        gross_profit_rate, tax_rate, percentage_rate, distribution_time, is_test, notes
    )

@verify_permission('add_kind')
@common_ajax_response
def add_record(request):
    company_id = request.POST.get('company_id')
    product = request.POST.get('product')
    service_id = request.POST.get('service_id')
    salesperson = request.POST.get('salesperson')
    price = request.POST.get('price')
    amount = request.POST.get('amount')
    total_price = request.POST.get('total_price')
    settlement_price = request.POST.get('settlement_price')
    gross_profit_rate = request.POST.get('gross_profit_rate')
    tax_rate = request.POST.get('tax_rate')
    percentage_rate = request.POST.get('percentage_rate')
    distribution_time = request.POST.get('distribution_time')
    state = request.POST.get('state')
    is_test = request.POST.get('is_test')
    is_test = True if is_test == '1' else False
    notes = request.POST.get('notes')

    flag, msg = OrderRecordBase().add_record(
        company_id, product, service_id, salesperson, price, 
        amount, total_price, settlement_price, gross_profit_rate,
        tax_rate, percentage_rate, distribution_time, state, is_test, notes
    )

    return flag, msg.id if flag == 0 else msg

@verify_permission('add_kind')
@common_ajax_response
def confirm_record(request):

    obj_id = request.POST.get('obj_id')
    ip = utils.get_clientip(request)

    return OrderRecordBase().confirm_record(obj_id, ip)

@verify_permission('add_kind')
@common_ajax_response
def drop_record(request):
    
    obj_id = request.POST.get('obj_id')

    return OrderRecordBase().drop_record(obj_id)





























