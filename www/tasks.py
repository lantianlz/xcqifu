# -*- coding: utf-8 -*-

import logging
import datetime
from celery.task import task


def async_send_email(emails, title, content, type='text'):
    '''
    @note: 由于调用较多，包装一层，用于控制是否异步调用
    '''
    from django.conf import settings
    if settings.LOCAL_FLAG:
        async_send_email_xcqifu_worker(emails, title, content, type)
    else:
        async_send_email_xcqifu_worker.delay(emails, title, content, type)


@task(queue='email_xcqifu_worker', name='email_xcqifu_worker.email_send')
def async_send_email_xcqifu_worker(emails, title, content, type='text'):
    from common import utils
    return utils.send_email(emails, title, content, type)


@task(queue='www_xcqifu_worker', name='www_xcqifu_worker.async_change_profile_from_weixin')
def async_change_profile_from_weixin(user, app_key, openid, qrscene=""):
    from www.account.interface import UserBase
    UserBase().change_profile_from_weixin(user, app_key, openid)
