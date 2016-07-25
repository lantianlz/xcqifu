# -*- coding: utf-8 -*-

import sys
import os

# 引入父目录来引入其他模块
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([os.path.abspath(os.path.join(SITE_ROOT, '../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../')),
                 ])
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'


import time
import json
import requests
import datetime
from django.conf import settings
from www.service.models import Kind, KindOpenInfo


def init_kind():
    kind_type_choices = Kind.kind_type_choices
    datas = [
        [
            {"name": u"下午茶", "slogan": u"你离有人文情怀的公司，还差一份下午茶", },
            {"name": u"工作餐", "slogan": u"要想小伙伴活干得好，饭首先得管饱", },
            {"name": u"生日会", "slogan": u"让定期举办的生日会也充满不一样的乐趣，布置和食物都交给我们吧", },
            {"name": u"礼品", "slogan": u"每逢佳节来一份礼品，展示一份心意", },
            {"name": u"饮用水", "slogan": u"老板，桶装水来10桶", },
        ],
        [
            {"name": u"团队旅游", "slogan": u"公司团队旅游的组织、策划、预定，不再为去哪儿感到焦虑", },
            {"name": u"素质拓展", "slogan": u"团队文化建设通过拓展训练是一个不错的方式", },
            {"name": u"团队聚餐", "slogan": u"岂止于吃吃吃，让你们的team building充满不一样的乐趣", },
        ],
        [
            {"name": u"名片制作", "slogan": u"好的名片，在这里制作", },
            {"name": u"物料制作", "slogan": u"产品宣传、DM单、户外展架在这里应有尽有", },
            {"name": u"易拉宝", "slogan": u"迎风扛一面易拉宝，线下地推利器", },
            {"name": u"服装定制", "slogan": u"T恤、工作服、卫衣全都可以在这里搞定", },
        ],
        [
            {"name": u"植物租赁", "slogan": u"装饰你的办公室，让你的眼前一片绿色", },
            {"name": u"办公用品", "slogan": u"在这里办公用品一站式搞定", },
            {"name": u"IT服务", "slogan": u"不再耽误程序猿哥哥的宝贵时间，请选择专业的IT服务商", },
            {"name": u"快递", "slogan": u"三通一达都在这里可以找到", },
            {"name": u"保洁", "slogan": u"让办公室持续保持干净", },
            {"name": u"机票预订", "slogan": u"订票从此更简单", },
        ],
        [
            {"name": u"注册代办", "slogan": u"注册代办", },
            {"name": u"财务代办", "slogan": u"财务代办", },
            {"name": u"社保代缴", "slogan": u"社保代缴", },
            {"name": u"商标注册", "slogan": u"商标注册", },
            {"name": u"法律顾问", "slogan": u"法律顾问", },
        ],
        [
            {"name": u"孵化器", "slogan": u"孵化器", },
            {"name": u"会议场地", "slogan": u"会议场地", },
            {"name": u"健康体检", "slogan": u"健康体检", },
            {"name": u"员工保险", "slogan": u"员工保险", },
            {"name": u"装修设计", "slogan": u"装修设计", },
        ],

    ]
    for i, data in enumerate(datas):
        for d in data:
            if Kind.objects.filter(name=d['name']):
                continue
            Kind.objects.create(name=d['name'], slogan=d['slogan'], kind_type=i)


def init_kind_open_info():
    for kind in Kind.objects.all():
        if KindOpenInfo.objects.filter(kind=kind, city_id=1974):
            continue
        KindOpenInfo.objects.create(kind=kind, city_id=1974, open_time=datetime.datetime.now())


if __name__ == '__main__':
    init_kind()
    init_kind_open_info()
