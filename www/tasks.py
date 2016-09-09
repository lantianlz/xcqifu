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
    UserBase().change_profile_from_weixin(user, app_key, openid, qrscene=qrscene)


@task(queue='www_xcqifu_worker', name='www_xcqifu_worker.async_send_invite_success_template_msg')
def async_send_invite_success_template_msg(openid, name, gender, regist_time):
    from www.weixin.interface import WeixinBase
    WeixinBase().send_invite_success_template_msg(openid, name, gender, regist_time)


@task(queue='www_xcqifu_worker', name='www_xcqifu_worker.async_send_verfy_info_notification_template_msg')
def async_send_verfy_info_notification_template_msg(openid, name, mobile, create_time, info):
    from www.weixin.interface import WeixinBase
    WeixinBase().send_verfy_info_notification_template_msg(openid, name, mobile, create_time, info)


@task(queue='www_xcqifu_worker', name='www_xcqifu_worker.async_send_verfy_result_template_msg')
def async_send_verfy_result_template_msg(openid, des, result, reason, remark):
    from www.weixin.interface import WeixinBase
    WeixinBase().send_verfy_result_template_msg(openid, des, result, reason, remark)


@task(queue='www_xcqifu_worker', name='www_xcqifu_worker.async_send_new_order_template_msg')
def async_send_new_order_template_msg(openid, name, mobile, create_time, service_name):
    from www.weixin.interface import WeixinBase
    WeixinBase().send_new_order_template_msg(openid, name, mobile, create_time, service_name)
