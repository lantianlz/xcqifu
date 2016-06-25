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

from www.account.interface import UserBase, ExternalTokenBase

DEFAULT_DB = 'default'

dict_err = {
    20101: u'',

}
dict_err.update(consts.G_DICT_ERROR)
