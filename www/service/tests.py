# -*- coding: utf-8 -*-

import os
import sys

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
# 引入父目录来引入其他模块
sys.path.extend([os.path.abspath(os.path.join(SITE_ROOT, '../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../')),
                 ])
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'


def main():
    import datetime
    from django.conf import settings
    from common import utils
    from www.weixin.interface import WeixinBase
    from www.tasks import async_send_email
    from pprint import pprint

    print datetime.datetime.now().date() - datetime.timedelta(days=7)

if __name__ == '__main__':
    main()
