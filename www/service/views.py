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
    city_id = request.session.get("city_id", 1974)
    data = kb.get_kind_list(city_id=city_id)
    print data

    # 类别样式对应字典
    CATEGORY_STYLE_DICT = {
        0: 'welfare',
        1: 'development',
        2: 'environment',
        3: 'materiel',
        4: 'company',
        5: 'other'
    }
    # 将样式加到每个类别里面
    for x in data:
        x.append(CATEGORY_STYLE_DICT[x[0]])

    # 转换成json
    data_json = json.dumps(data)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_list(request, template_name='mobile/service/service_list.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def service_detail(request, service_id, template_name='mobile/service/service_detail.html'):
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
