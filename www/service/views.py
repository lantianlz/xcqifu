# -*- coding: utf-8 -*-

import json
import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import common_ajax_response, member_required, request_limit_by_ip, auto_select_template
from www.service.interface import KindBase, ServiceBase
from www.weixin.interface import WeixinBase, Sign


kb = KindBase()
sb = ServiceBase()


@auto_select_template
def index(request, template_name='mobile/index.html'):
    city_id = request.session.get("city_id", 1974)
    data = kb.get_kind_list(city_id=city_id)
    # print data

    # 转换成json
    data_json = json.dumps(data)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_list(request, kind_id, template_name='mobile/service/service_list.html'):
    services = sb.get_service_by_kind(kind_id)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_detail(request, service_id, template_name='mobile/service/service_detail.html'):
    service = sb.get_service_by_id(service_id)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
