# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings


class Kind(models.Model):
    '''
    @note: 类别
    '''
    kind_type_choices = ((0, u"餐饮福利"), (1, u"员工活动"), (2, u"宣传物料"), (3, u"日常办公"), (4, u"公司代办"), (5, u"其他"))

    name = models.CharField(verbose_name=u"名称", max_length=32, unique=True)
    slogan = models.CharField(verbose_name=u"slogan", max_length=256)
    kind_type = models.IntegerField(verbose_name=u"类别", default=0, choices=kind_type_choices)

    hot = models.IntegerField(verbose_name=u"热度", default=0)
    state = models.BooleanField(verbose_name=u"状态是否正常", default=True)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "create_time"]

    def get_url(self):
        return u'/kind/%s' % self.id

    def get_full_url(self):
        return u'%s%s' % (settings.MAIN_DOMAIN, self.get_url())


class KindOpenInfo(models.Model):
    '''
    @note: 类别开放信息
    '''
    kind = models.ForeignKey("Kind")
    city_id = models.IntegerField(verbose_name=u"所属城市")
    open_time = models.DateTimeField(verbose_name=u"开放时间",  db_index=True)

    class Meta:
        unique_together = [("kind", "city_id"), ]


class Service(models.Model):
    '''
    @note: 服务商
    '''
    level_choices = ((0, u"普通"), (0, u"自营"), (0, u"优质"))

    name = models.CharField(verbose_name=u"名称", max_length=32, db_index=True)
    kind = models.ForeignKey("Kind")
    logo = models.CharField(verbose_name=u"logo", max_length=256)
    city_id = models.IntegerField(verbose_name=u"所属城市")
    summary = models.CharField(verbose_name=u"摘要", max_length=256)
    des = models.TextField(verbose_name=u"简介")
    imgs = models.TextField(verbose_name=u"轮播图集中存放")

    service_area = models.CharField(verbose_name=u"服务范围", max_length=256)
    tel = models.CharField(verbose_name=u"联系电话", max_length=256, null=True)
    addr = models.CharField(verbose_name=u"地址", max_length=256, null=True)
    longitude = models.CharField(verbose_name=u"经度", max_length=32, null=True)
    latitude = models.CharField(verbose_name=u"纬度", max_length=32, null=True)
    join_time = models.DateTimeField(verbose_name=u"入驻时间", db_index=True, null=True)

    recommend_user_id = models.CharField(verbose_name=u"推荐人", max_length=32, db_index=True, null=True)
    recommend_des = models.TextField(verbose_name=u"推荐语", null=True)
    like_count = models.IntegerField(verbose_name=u"点赞次数", default=0, db_index=True)
    order_count = models.IntegerField(verbose_name=u"预订次数", default=0, db_index=True)
    level = models.IntegerField(verbose_name=u"供应商等级", default=0, choices=level_choices)
    is_show = models.BooleanField(verbose_name=u"是否在列表页显示", default=True)
    state = models.BooleanField(verbose_name=u"状态是否正常", default=True)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "-create_time"]
        unique_together = [("kind", "name"), ]

    def get_tel(self):
        return self.tel or "4008-920-310"

    def get_url(self):
        return u'/service/%s' % self.id


class Product(models.Model):
    '''
    @note: 产品
    '''
    name = models.CharField(verbose_name=u"名称", max_length=32, db_index=True)
    service = models.ForeignKey("Service")
    cover = models.CharField(verbose_name=u"封面", max_length=256, null=True)
    summary = models.TextField(verbose_name=u"摘要信息", null=True)
    des = models.TextField(verbose_name=u"简介")
    price = models.DecimalField(verbose_name=u"价格", max_digits=20, decimal_places=2, db_index=True)
    params = models.TextField(verbose_name=u"额外参数", null=True)

    state = models.BooleanField(verbose_name=u"状态是否正常", default=True)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "-create_time"]
        unique_together = [("name", "service"), ]

    def get_url(self):
        return u'/service/product/%s' % self.id


class Order(models.Model):
    '''
    @note: 预约订单
    '''
    state_choices = ((0, u"待处理"), (1, u"接单中"), (2, u"已完成"))

    user_id = models.CharField(max_length=32, db_index=True)
    service = models.ForeignKey("Service")
    product = models.ForeignKey("Product", null=True)   # 产品字段为空表示直接预约供应商

    price = models.DecimalField(verbose_name=u"价格", max_digits=20, decimal_places=2, db_index=True)
    state = models.BooleanField(verbose_name=u"状态是否正常", default=0, choices=state_choices)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "-create_time"]


class Zan(models.Model):
    '''
    @note: 赞过的供应商，用于收藏
    '''
    user_id = models.CharField(max_length=32, db_index=True)
    service = models.ForeignKey("Service")

    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        unique_together = [("user_id", "service"), ]
        ordering = ["-id"]
