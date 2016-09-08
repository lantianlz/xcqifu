# -*- coding: utf-8 -*-

import os
import sys

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
# 引入父目录来引入其他模块
sys.path.extend([os.path.abspath(os.path.join(SITE_ROOT, '../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../')),
                 ])
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'


user_id = 'f762a6f5d2b711e39a09685b35d0bf16'


def main():
    import time
    import datetime
    from django.conf import settings
    from common import utils
    from www.weixin.interface import WeixinBase
    from www.tasks import async_send_email
    from pprint import pprint

    wb = WeixinBase()
    app_key = "xcqifu_test"
    to_user = 'oZy3hskE524Y2QbLgY2h3VnI3Im8'

    app_key = "xcqifu"
    to_user = 'odZBHxIYA_4vMMzeUU-2QU3NyAa4'
    # content = (u'古人云：鸟随鸾凤飞腾远，人伴贤良品质高。\n')

    # print wb.send_msg_to_weixin(content, to_user, app_key)

    # context = {'reset_url': '%s/reset_password?code=%s' % (settings.MAIN_DOMAIN, "123"), }
    # print async_send_email("web@3-10.cc", u'来自小橙企服', utils.render_email_template('email/reset_password.html', context), 'html')

    # pprint(wb.get_user_info(app_key, to_user))
    # pprint(wb.get_qr_code_ticket(app_key))

    # print wb.send_balance_insufficient_template_msg(to_user, u"账户已达「1000」最高透支额，请及时充值", u"成都大橙科技有限公司", u"-1001",
    #                                                 u"感谢您的支持，祝工作愉快")

    # print wb.get_qr_code_ticket(app_key, is_limit=True, scene_str="invite_0")
    print datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    main()
