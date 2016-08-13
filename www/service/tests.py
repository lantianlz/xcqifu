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

    from www.service.interface import ServiceBase, ProductBase, ZanBase

    sb = ServiceBase()
    pb = ProductBase()
    zb = ZanBase()

    ps1 = dict(name=u"三点十分", kind_id=1, logo="http://static.3-10.cc/img/logo.png", city_id=1974, summary=u"三点十分，企业下午茶服务专家",
               des=u"""
              三点十分是一家专注于企业下午茶点服务的互联网公司，下午茶O2O服务领跑者
			  按需定制企业下午茶套餐，免费配送上门，由资深互联网团队倾心打造，一流的水果供应商和行业领先的食品加工厂联袂为企业带来新鲜的水果和可口的点心，
			  资深营养师为你精心搭配，确保营养均衡
              """, imgs='<img src="/static/img/service/detail-1.jpg">', service_area=u"成都高新区", tel="4008-920-310", addr=u"成都市天府五街菁蓉国际广场",
               longitude="104.069271", latitude="30.544437", join_time="2016-07-19", )
    ps2 = dict(name=u"肉多多", kind_id=2, logo="http://oalrluiy0.bkt.clouddn.com/4.pic.jpg", city_id=1974, summary=u"肉多多，好吃的工作餐",
               des=u"""
              肉多多，好吃的工作餐
              """, imgs='<img src="/static/img/service/detail-1.jpg">', service_area=u"成都高新区", tel="4008-920-310", addr=u"成都市天府五街菁蓉国际广场",
               longitude="104.069271", latitude="30.544437", join_time="2016-07-19", )

    # print sb.add_service(**ps1)
    # print sb.add_service(**ps2)

    # print pb.add_product(name=u"三分果切", service_id=2, des=u"250g每盒", price=7,
    #                      cover="http://img0.3-10.cc/item_bafa4ee26f2c11e587c800163e001bb1", summary=u"分量适中，味道好")
    # print pb.add_product(name=u"两分果切", service_id=2, des=u"200g每盒", price=5,
    #                      cover="http://img0.3-10.cc/item_69473dbe524b11e6856d00163e001bb1", summary=u"两种水果混搭")

    print zb.add_zan(user_id="2fda4e0053da11e6bd8ad0a637ea4c03", service_id=2)
    print zb.add_zan(user_id="2fda4e0053da11e6bd8ad0a637ea4c03", service_id=3)
    # print zb.cancel_zan(user_id="2fda4e0053da11e6bd8ad0a637ea4c03", service_id=2)


if __name__ == '__main__':
    main()
