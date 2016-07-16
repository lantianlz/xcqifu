# -*- coding: utf-8 -*-

import json
import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import common_ajax_response, member_required, request_limit_by_ip
from www.service.interface import KindBase
from www.weixin.interface import WeixinBase, Sign


kb = KindBase()


def index(request, template_name='mobile/index.html'):
    data = kb.get_kind_list()
    print data

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_list(request, template_name='mobile/service/service_list.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_detail(request, service_id, template_name='mobile/service/service_detail.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
