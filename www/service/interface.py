# -*- coding: utf-8 -*-

import datetime
import logging
import time
import random
import decimal
from django.db import transaction
from django.db.models import Sum, Count
from django.utils.encoding import smart_unicode
from django.conf import settings

from common import utils, debug, validators, cache, raw_sql
from www.misc.decorators import cache_required
from www.misc import consts

from www.service.models import Kind, KindOpenInfo

DEFAULT_DB = 'default'

dict_err = {
    20101: u'',

}
dict_err.update(consts.G_DICT_ERROR)


class KindBase(object):

    def __init__(self):
        self.cache = cache.Cache()

    def __del__(self):
        del self.cache

    # @cache_required(cache_key='kind_list_%s', expire=3600 * 12)
    def get_kind_list(self, city_id=1974):
        """
        @note:获取首页所需列表
        data = [(0, u"餐饮福利", u"下午茶、生日会、工作餐、礼品", True, [{"id": 1, "name": u"下午茶", "is_open": True, "is_new": True}, ]),
                ]
        """
        data = []
        kois = list(KindOpenInfo.objects.filter(city_id=city_id))

        def _get_kind_open(kind):
            for koi in kois:
                if koi.kind_id == kind.id:
                    return koi

        for kt in Kind.kind_type_choices:
            is_new_total = False
            ks = []
            kinds = Kind.objects.filter(kind_type=kt[0])
            lst_kind_name = []
            for kind in kinds:
                koi = _get_kind_open(kind)
                is_new = True if koi.open_time.date() >= (datetime.datetime.now().date() - datetime.timedelta(days=7)) else False
                if is_new:
                    is_new_total = True
                ks.append(dict(id=kind.id, name=kind.name, is_open=True if koi else False, is_new=is_new))
                lst_kind_name.append(kind.name)

            big_kind_summary = u"、".join(lst_kind_name)
            ls = (kt[0], kt[1], big_kind_summary, is_new_total, ks)
            data.append(ls)

        return data
