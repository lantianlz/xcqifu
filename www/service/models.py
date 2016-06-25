# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
import datetime
import decimal


class Service(models.Model):

    '''
    @note: 服务商
    '''
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "-create_time"]
