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

    from www.service.interface import ServiceBase

    # print datetime.datetime.now().date() - datetime.timedelta(days=7)
    sb = ServiceBase()
    ps = dict(name=u"三点十分", kind_id=1, logo="http://static.3-10.cc/img/logo.png", city_id=1974, summary=u"三点十分，企业下午茶服务专家",
              des=u"""
              三点十分是一家专注于企业下午茶点服务的互联网公司，下午茶O2O服务领跑者
			  按需定制企业下午茶套餐，免费配送上门，由资深互联网团队倾心打造，一流的水果供应商和行业领先的食品加工厂联袂为企业带来新鲜的水果和可口的点心，
			  资深营养师为你精心搭配，确保营养均衡
              """, imgs='<img src="/static/img/service/detail-1.jpg">', service_area=u"成都高新区", tel="4008-920-310", addr=u"成都市天府五街菁蓉国际广场",
              longitude="104.069271", latitude="30.544437", join_time="2016-07-19", )
    print sb.add_service(**ps)


if __name__ == '__main__':
    main()
