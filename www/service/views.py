# -*- coding: utf-8 -*-

import json
import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import common_ajax_response, member_required, company_manager_required_for_request, request_limit_by_ip
from www.account.interface import UserBase
from www.weixin.interface import WeixinBase, Sign


@member_required
def index(request):
    '''
    公司管理首页
    '''
    # 判断是否是公司管理员
    cm = CompanyManagerBase().get_cm_by_user_id(request.user.id)
    if cm:
        return HttpResponseRedirect("/company/%s/record" % cm.company.id)

    err_msg = u'权限不足，你还不是公司管理员，如有疑问请联系小橙企服客服'
    return render_to_response('error.html', locals(), context_instance=RequestContext(request))
