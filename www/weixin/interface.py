# -*- coding: utf-8 -*-
import random
import string
import hashlib
import time
import requests
import json
import logging
from django.conf import settings
from pyquery import PyQuery as pq

from common import cache, debug
from www.misc import consts
from www.weixin.weixin_config import dict_weixin_app


dict_err = {
    70100: u'发送模板消息异常',
}
dict_err.update(consts.G_DICT_ERROR)


weixin_api_url = 'https://api.weixin.qq.com'


class WeixinBase(object):

    def __init__(self):
        self.cache = cache.Cache()

    def __del__(self):
        del self.cache

    def init_app_key(self, default_value="xcqifu"):
        return "xcqifu_test" if settings.LOCAL_FLAG else default_value

    def get_app_id(self):
        return dict_weixin_app[self.init_app_key()]['app_id']

    def get_base_text_response(self):
        '''
        @note: 文字信息模板
        '''
        return u'''
        <xml>
        <ToUserName><![CDATA[%(to_user)s]]></ToUserName>
        <FromUserName><![CDATA[%(from_user)s]]></FromUserName>
        <CreateTime>%(timestamp)s</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[%(content)s]]></Content>
        </xml>
        '''

    def get_base_news_response(self, items=None):
        '''
        @note: 图文信息模板
        '''
        return u'''
        <xml>
        <ToUserName><![CDATA[%(to_user)s]]></ToUserName>
        <FromUserName><![CDATA[%(from_user)s]]></FromUserName>
        <CreateTime>%(timestamp)s</CreateTime>
        <MsgType><![CDATA[news]]></MsgType>
        <ArticleCount>%(articles_count)s</ArticleCount>
        <Articles>
        ''' + (items or self.get_base_news_item_response()) + \
            '''
        </Articles>
        </xml>
        '''

    def get_base_news_item_response(self):
        return u'''
        <item>
        <Title><![CDATA[%(title)s]]></Title>
        <Description><![CDATA[%(des)s]]></Description>
        <PicUrl><![CDATA[%(picurl)s]]></PicUrl>
        <Url><![CDATA[%(hrefurl)s]]></Url>
        </item>
        '''

    def get_base_content_response(self, to_user, from_user, content):
        base_xml = self.get_base_text_response()
        return base_xml % dict(to_user=from_user, from_user=to_user, timestamp=int(time.time()), content=content)

    def get_error_response(self, to_user, from_user, error_info):
        base_xml = self.get_base_text_response()
        return base_xml % dict(to_user=from_user, from_user=to_user, timestamp=int(time.time()), content=error_info)

    def get_subscribe_event_response(self, to_user, from_user):
        content = (u'一站式搞定行政事务，尽在小橙企服，'
                   u'立即访问底部菜单体验。'
                   )
        return self.get_base_content_response(to_user, from_user, content=content)

    def get_customer_service_response(self, to_user, from_user):
        return u'''
        <xml>
        <ToUserName><![CDATA[%(to_user)s]]></ToUserName>
        <FromUserName><![CDATA[%(from_user)s]]></FromUserName>
        <CreateTime>%(timestamp)s</CreateTime>
        <MsgType><![CDATA[transfer_customer_service]]></MsgType>
        </xml>
        ''' % dict(to_user=from_user, from_user=to_user, timestamp=int(time.time()))

    def format_input_xml(self, xml):
        '''
        @note: 标签替换为小写，以便pyquery能识别
        '''
        for key in ['ToUserName>', 'FromUserName>', 'CreateTime>', 'MsgType>', 'Content>', 'MsgId>', 'PicUrl>',
                    'MediaId>', 'Format>', 'ThumbMediaId>', 'Event>', 'EventKey>', 'Ticket>', 'Recognition>',
                    'DeviceID>', 'SessionID>', 'DeviceType>', 'OpenID>']:
            xml = xml.replace(key, key.lower())
        return xml

    def get_response(self, xml):
        from www.account.interface import UserBase

        xml = self.format_input_xml(xml)
        jq = pq(xml)
        to_user = jq('tousername')[0].text
        from_user = jq('fromusername')[0].text
        events = jq('event')
        app_key = self.get_app_key_by_app_type(to_user)
        logging.error(u'收到一个来自app：%s 的请求' % app_key)

        if "test" in app_key:   # 剔除测试公众号发送信息
            return

        # 事件
        if events:
            event = events[0].text.lower()
            # 关注或者扫码登陆事件
            if event in ('scan', 'subscribe'):
                event_key = u""
                event_keys = jq('eventkey')
                if event_keys:
                    event_key = event_keys[0].text

                event_key = event_key.replace("qrscene_", "")
                # 首次关注自动注册用户
                if event == "subscribe":
                    UserBase().regist_by_weixin(from_user, app_key, qrscene=event_key)

                tickets = jq('ticket')
                if tickets:
                    ticket = tickets[0].text

                    if not event_key.startswith("invite"):
                        errcode, errmsg = UserBase().login_by_weixin_qr_code(ticket, from_user, app_key)
                        return self.get_base_content_response(to_user, from_user, errmsg)
                    else:
                        return self.get_base_content_response(to_user, from_user, u"终于来到小橙企服，邀请你使用的朋友一定很开心，立即用起来吧")
                return self.get_subscribe_event_response(to_user, from_user)  # 关注信息

            elif event in ('click', ):
                event_key = jq('eventkey')[0].text.lower()
                if event_key == 'feedback':
                    content = (u'欢迎小伙伴们踊跃反馈意见，你的意见一经采纳，必有好礼相送。\n'
                               u'反馈方法：直接在此微信服务号中输入你的金玉良言即可，客服人员会及时跟进哦'
                               )
                    return self.get_base_content_response(to_user, from_user, content=content)
            elif event in ('unsubscribe'):
                # 更新是否关注微信状态
                from www.account.interface import ExternalTokenBase
                ExternalTokenBase().update_is_sub_weixin(from_user, False)

        # 文字识别
        msg_types = jq('msgtype')
        if msg_types:
            msg_type = msg_types[0].text
            if msg_type == 'text':
                content = jq('content')[0].text.strip()
                logging.error(u'收到用户发送的文本数据，内容如下：%s' % content)
                return self.get_customer_service_response(to_user, from_user)   # 多客服接管

    def get_app_key_by_app_type(self, app_type):
        for key in dict_weixin_app:
            if dict_weixin_app[key]['app_type'] == app_type:
                return key
        raise Exception, u'app_key not found by: %s' % app_type

    def send_msg_to_weixin(self, content, to_user, app_key, msg_type='text', img_info=''):
        '''
        @note: 发送信息给微信
        '''
        # json的dumps字符串中中文微信不识别，修改为直接构造
        if msg_type == 'text':
            data = u'{"text": {"content": "%s"}, "msgtype": "%s", "touser": "%s"}' % (content, msg_type, to_user)
        else:
            data = u'{"news":{"articles": %s}, "msgtype":"%s", "touser": "%s"}' % (img_info, msg_type, to_user)

        data = data.encode('utf8')

        access_token = self.get_weixin_access_token(app_key)
        url = '%s/cgi-bin/message/custom/send?access_token=%s' % (weixin_api_url, access_token)

        for i in range(3):
            try:
                r = requests.post(url, data=data, timeout=5, verify=False)
                break
            except:
                pass

        r.raise_for_status()
        content = json.loads(r.content)
        logging.error('send msg to weixin resp is %s' % (content,))

    def get_weixin_access_token(self, app_key):
        # 本地调试模式不走缓存
        # if not settings.LOCAL_FLAG:
        if False:
            key = 'weixin_access_token_for_%s' % app_key
            access_token = self.cache.get(key)
            if access_token is None:
                access_token, expires_in = self.get_weixin_access_token_directly(app_key)
                if access_token:
                    self.cache.set(key, access_token, int(expires_in))
        else:
            access_token, expires_in = self.get_weixin_access_token_directly(app_key)
        return access_token

    def get_weixin_access_token_directly(self, app_key):
        access_token, expires_in = '', 0
        content = ''
        url = '%s/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (weixin_api_url, dict_weixin_app[app_key]['app_id'],
                                                                                    dict_weixin_app[app_key]['app_secret'])
        try:
            r = requests.get(url, timeout=20, verify=False)
            content = r.content
            r.raise_for_status()
            content = json.loads(content)
            access_token = content['access_token']
            expires_in = content['expires_in']
        except Exception, e:
            logging.error(u'get_weixin_access_token rep is %s' % content)
            debug.get_debug_detail(e)
        assert access_token
        return access_token, expires_in

    def get_user_info(self, app_key, openid):
        """
        @note: 获取一关注公众号的用户信息
        """
        access_token = self.get_weixin_access_token(app_key)
        url = '%s/cgi-bin/user/info?access_token=%s&openid=%s' % (weixin_api_url, access_token, openid)
        data = {}
        try:
            r = requests.get(url, timeout=20, verify=False)
            text = r.text
            r.raise_for_status()
            data = json.loads(text)
            if data.get("errmsg") or data.get("subscribe") == 0:
                logging.error("error user info data is:%s" % data)
                data = {}
        except Exception, e:
            debug.get_debug_detail_and_send_email(e)
        return data

    def get_qr_code_ticket(self, app_key, expire=300, is_limit=False, scene_str=""):
        """
        @note: 获取二维码对应的ticket
        """
        access_token = self.get_weixin_access_token(app_key)
        url = '%s/cgi-bin/qrcode/create?access_token=%s' % (weixin_api_url, access_token)
        if not is_limit:
            data = u'{"expire_seconds":%s, "action_name":"QR_SCENE", "action_info": {"scene": {"scene_id": %s}}' % (expire, int(time.time() * 1000))
        else:
            data = u'{"action_name":"QR_LIMIT_STR_SCENE", "action_info": {"scene": {"scene_str": "%s"}}' % scene_str
        data = data.encode('utf8')

        result = {}
        try:
            r = requests.post(url, data=data, timeout=20, verify=False)
            text = r.text
            r.raise_for_status()
            result = json.loads(text)
            if result.get("errmsg") or result.get("subscribe") == 0:
                logging.error("error create_qr_code result is:%s" % result)
                result = {}
        except Exception, e:
            debug.get_debug_detail(e)
        return result

    def send_template_msg(self, app_key, openid, content, template_id, jump_url=''):
        """
        @note: 发送模板消息
        """
        access_token = self.get_weixin_access_token(app_key)
        url = '%s/cgi-bin/message/template/send?access_token=%s' % (weixin_api_url, access_token)

        data = u'''
        {
           "touser":"%(openid)s",
           "template_id":"%(template_id)s",
           "url":"%(jump_url)s",
           "data":%(content)s
       }
       ''' % dict(openid=openid, template_id=template_id, jump_url=jump_url, content=content)
        data = data.encode('utf8')

        errcode, errmsg = 0, dict_err.get(0)
        try:
            r = requests.post(url, data=data, timeout=20, verify=False)
            text = r.text
            r.raise_for_status()
            result = json.loads(text)
            errcode, errmsg = result["errcode"], result["errmsg"]
        except Exception, e:
            debug.get_debug_detail(e)
            errcode, errmsg = 70100, dict_err.get(70100)
        return errcode, errmsg

    def send_invite_success_template_msg(self, openid, name, gender, regist_time, app_key=None):
        """
        @note: 发送邀请注册成功提醒消息
        """
        template_id = "ANMe8H4Ii465YJKIUYHhUTiaqgBa9XADFQY-CW7UXMI"
        app_key = app_key or self.init_app_key()
        content = u'''
         {
            "first": {
                "value":"干得漂亮，成功邀请新用户一枚，请尽快联系TA填写认证信息",
                "color":"#EF8A55"
            },
            "keyword1": {
                "value":"%(name)s",
                "color":"#999999"
            },
            "keyword2":{
                "value":"%(gender)s",
                "color":"#999999"
            },
            "keyword3":{
                "value":"%(regist_time)s",
                "color":"#999999"
            },
            "remark":{
                "value":"点击查看所有邀请记录",
                "color":"#999999"
            }
         }
        ''' % dict(name=name, gender=gender, regist_time=regist_time)

        jump_url = "%s/account/recommendation" % settings.MAIN_DOMAIN
        return self.send_template_msg(app_key, openid, content, template_id, jump_url=jump_url)

    def send_todo_list_template_msg(self, openid, info, job, priority, remark, app_key=None):
        '''
        发送待办任务提醒通知
        '''
        template_id = "-rAhCPV9q3lUoslRYQUlHhpwvJXraX7BDuJgfKW2Bss"
        app_key = app_key or self.init_app_key()
        content = u'''
         {
            "first": {
                "value":"%(info)s",
                "color":"#EF7B32"
            },
            "keyword1": {
                "value":"%(job)s",
                "color":"#000000"
            },
            "keyword2":{
                "value":"%(priority)s",
                "color":"#000000"
            },
            "remark":{
                "value":"%(remark)s",
                "color":"#000000"
            }
         }
        ''' % dict(info=info, job=job, priority=priority, remark=remark)

        return self.send_template_msg(app_key, openid, content, template_id)

    def get_weixin_jsapi_ticket(self, app_key):
        # 本地调试模式不走缓存
        if not settings.LOCAL_FLAG:
            key = 'weixin_jsapi_ticket_for_%s' % app_key
            ticket = self.cache.get(key)
            if ticket is None:
                ticket, expires_in = self.get_weixin_jsapi_ticket_directly(app_key)
                if ticket:
                    self.cache.set(key, ticket, int(expires_in))
        else:
            ticket, expires_in = self.get_weixin_jsapi_ticket_directly(app_key)
        return ticket

    def get_weixin_jsapi_ticket_directly(self, app_key):
        ticket, expires_in = '', 0
        content = ''

        url = '%s/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % (weixin_api_url, self.get_weixin_access_token(app_key))
        try:
            r = requests.get(url, timeout=20, verify=False)
            content = r.content
            r.raise_for_status()
            content = json.loads(content)
            ticket = content['ticket']
            expires_in = content['expires_in']
        except Exception, e:
            logging.error(u'get_weixin_jsapi_ticket rep is %s' % content)
            debug.get_debug_detail(e)
        assert ticket
        return ticket, expires_in


class Sign(object):

    def __init__(self, jsapi_ticket, url):
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': jsapi_ticket,
            'timestamp': self.__create_timestamp(),
            'url': url
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        string = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(string).hexdigest()
        return self.ret
