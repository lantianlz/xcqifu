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
        ordering = ["-open_time"]


class Service(models.Model):
    '''
    @note: 服务商
    '''
    level_choices = ((0, u"普通"), (1, u"自营"), (2, u"优质"))

    name = models.CharField(verbose_name=u"名称", max_length=32, db_index=True)
    kind = models.ForeignKey("Kind")
    logo = models.CharField(verbose_name=u"logo", max_length=256)
    city_id = models.IntegerField(verbose_name=u"所属城市")
    summary = models.CharField(verbose_name=u"摘要", max_length=256)
    des = models.TextField(verbose_name=u"简介")
    imgs = models.TextField(verbose_name=u"轮播图集中存放")

    service_area = models.CharField(verbose_name=u"覆盖区域", max_length=256)
    tel = models.CharField(verbose_name=u"联系电话", max_length=256, null=True)
    addr = models.CharField(verbose_name=u"地址", max_length=256, null=True)
    longitude = models.CharField(verbose_name=u"经度", max_length=32, null=True)
    latitude = models.CharField(verbose_name=u"纬度", max_length=32, null=True)
    join_time = models.DateTimeField(verbose_name=u"入驻时间", db_index=True, null=True)

    recommend_user_id = models.CharField(verbose_name=u"推荐人", max_length=32, db_index=True, null=True)
    recommend_des = models.TextField(verbose_name=u"推荐语", null=True)
    zan_count = models.IntegerField(verbose_name=u"点赞次数", default=0, db_index=True)
    order_count = models.IntegerField(verbose_name=u"预订次数", default=0, db_index=True)
    level = models.IntegerField(verbose_name=u"供应商等级", default=0, choices=level_choices)
    is_show = models.BooleanField(verbose_name=u"是否在列表页显示", default=True)
    state = models.BooleanField(verbose_name=u"状态是否正常", default=True)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["sort", "create_time"]
        unique_together = [("kind", "name"), ]

    def get_tel(self):
        return self.tel or "4008-920-310"

    def get_url(self):
        return u'/service/%s' % self.id

    def get_covers(self):
        import re
        return re.compile('<img .*?src=[\"\'](.+?)[\"\']').findall(self.imgs)

    def get_format_des(self):
        des = ""

        for x in self.des.split('\r\n'):
            des += "<p>%s</p>" % x

        return des
        # return self.des.replace('\r\n', '<br/>')


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
    state = models.IntegerField(verbose_name=u"状态是否正常", default=0, choices=state_choices)
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


class Company(models.Model):

    '''
    公司信息
    '''
    state_choices = ((0, u"停用"), (1, u"正常"))

    name = models.CharField(verbose_name=u"名称", max_length=128, unique=True)
    short_name = models.CharField(verbose_name=u"简称", max_length=128, null=True)
    logo = models.CharField(verbose_name=u"logo", max_length=256, null=True)
    des = models.TextField(verbose_name=u"简介", null=True)
    staff_name = models.CharField(verbose_name=u"企业联系人", max_length=16, null=True)
    mobile = models.CharField(verbose_name=u"手机", max_length=32, null=True)
    tel = models.CharField(verbose_name=u"座机", max_length=32, null=True)
    addr = models.CharField(verbose_name=u"地址", max_length=256, null=True)
    person_count = models.IntegerField(verbose_name=u"员工总数", default=0)
    city_id = models.IntegerField(verbose_name=u"所属城市", default=0)
    state = models.IntegerField(verbose_name=u"状态", default=1, db_index=True, choices=state_choices)
    sort = models.IntegerField(verbose_name=u"排序", default=0)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    def get_logo(self):
        return self.logo if self.logo else '%simg/logo.png' % settings.MEDIA_URL

    def combine_name(self):
        '''
        组合名字：
        成都乐动科技有点公司 [ 咕咚 ]
        '''
        return '%s [ %s ]' % (self.name, self.short_name or '-')

    class Meta:
        ordering = ["sort", "-create_time"]


class CompanyManager(models.Model):
    company = models.ForeignKey("Company")
    user_id = models.CharField(verbose_name=u"管理员id", max_length=32, db_index=True)
    role = models.IntegerField(verbose_name=u"角色", default=0, db_index=True)

    class Meta:
        unique_together = [("company", "user_id"), ]
        ordering = ["company"]

class CashAccount(models.Model):

    '''
    @note: 现金账户
    '''
    company = models.ForeignKey("Company", unique=True)
    balance = models.DecimalField(verbose_name=u"最新余额", max_digits=20, decimal_places=2, default=0, db_index=True)
    max_overdraft = models.DecimalField(verbose_name=u"最大透支额", max_digits=20, decimal_places=2, default=1000, db_index=True)

    class Meta:
        ordering = ['balance', 'id']

class CashRecord(models.Model):

    '''
    @note: 现金账户流水
    '''
    operation_choices = ((0, u"充值"), (1, u"消费"))

    cash_account = models.ForeignKey("CashAccount")
    value = models.DecimalField(verbose_name=u"操作金额", max_digits=20, decimal_places=2, db_index=True)
    current_balance = models.DecimalField(verbose_name=u"当时余额", max_digits=20, decimal_places=2, db_index=True)
    operation = models.IntegerField(verbose_name=u"操作类型", choices=operation_choices, db_index=True)
    notes = models.CharField(verbose_name=u"备注", max_length=256)
    is_invoice = models.IntegerField(verbose_name=u"是否记录开票金额", default=1, null=True, db_index=True)
    ip = models.CharField(verbose_name=u"ip", max_length=32, null=True)
    create_time = models.DateTimeField(verbose_name=u"流水时间", auto_now_add=True, db_index=True) 

    class Meta:
        ordering = ['-id']


class ServiceCashAccount(models.Model):

    '''
    @note: 供货商现金账户
    '''
    service = models.ForeignKey("Service", unique=True)
    balance = models.DecimalField(verbose_name=u"最新余额", max_digits=20, decimal_places=2, default=0, db_index=True)

    class Meta:
        ordering = ['-balance', 'id']


class ServiceCashRecord(models.Model):

    '''
    @note: 供货商现金账户流水
    '''
    operation_choices = ((0, u"入账"), (1, u"转出"))

    cash_account = models.ForeignKey("ServiceCashAccount")
    value = models.DecimalField(verbose_name=u"操作金额", max_digits=20, decimal_places=2, db_index=True)
    current_balance = models.DecimalField(verbose_name=u"当时余额", max_digits=20, decimal_places=2, db_index=True)
    operation = models.IntegerField(verbose_name=u"操作类型", choices=operation_choices, db_index=True)
    notes = models.CharField(verbose_name=u"备注", max_length=256)
    ip = models.CharField(verbose_name=u"ip", max_length=32, null=True)
    order_id = models.CharField(verbose_name=u"订单流水id", max_length=32, null=True)
    create_time = models.DateTimeField(verbose_name=u"流水时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-id']



class OrderRecord(models.Model):

    '''
    '''
    state_choices = ((0, u"准备中"), (1, u"已完成"), (2, u"作废"))
    order_no = models.CharField(verbose_name=u"订单号", max_length=32, db_index=True)
    company = models.ForeignKey("Company")
    product = models.CharField(verbose_name=u"产品名称", max_length=32)
    service = models.ForeignKey("Service")
    salesperson = models.CharField(verbose_name=u"销售员id", max_length=32, db_index=True)

    price = models.DecimalField(verbose_name=u"单价", max_digits=8, decimal_places=2)
    amount = models.IntegerField(verbose_name=u"数量")
    total_price = models.DecimalField(verbose_name=u"销售总价", max_digits=10, decimal_places=2)
    settlement_price = models.DecimalField(verbose_name=u"结算总价", max_digits=10, decimal_places=2)
    gross_profit_rate = models.DecimalField(verbose_name=u"毛利率", max_digits=6, decimal_places=2)
    # gross_profit = models.DecimalField(verbose_name=u"毛利", max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(verbose_name=u"税率", max_digits=6, decimal_places=2)
    # tax = models.DecimalField(verbose_name=u"税费", max_digits=10, decimal_places=2)
    # net_rate = models.DecimalField(verbose_name=u"净利率", max_digits=6, decimal_places=2)
    # net = models.DecimalField(verbose_name=u"净利", max_digits=10, decimal_places=2)
    percentage_rate = models.DecimalField(verbose_name=u"提成比率", max_digits=6, decimal_places=2)
    # percentage = models.DecimalField(verbose_name=u"提成", max_digits=10, decimal_places=2)
    # net_income_rate = models.DecimalField(verbose_name=u"净收益比率", max_digits=10, decimal_places=2)
    # net_income = models.DecimalField(verbose_name=u"净收益", max_digits=10, decimal_places=2)
    state = models.IntegerField(verbose_name=u"状态", choices=state_choices, db_index=True)
    is_test = models.BooleanField(verbose_name=u"是否试餐", default=False)
    notes = models.CharField(verbose_name=u"备注", max_length=256, null=True)
    distribution_time = models.DateTimeField(verbose_name=u"配送时间", db_index=True)
    confirm_time = models.DateTimeField(verbose_name=u"确认时间", null=True)
    create_time = models.DateTimeField(verbose_name=u"创建时间", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-distribution_time']

    def smart_price(self):
        '''
        单价
        '''
        return round(self.price, 2)

    def smart_total_price(self):
        '''
        销售总价
        '''
        return round(self.total_price, 2)

    def smart_settlement_price(self):
        '''
        结算总价
        '''
        return round(self.settlement_price, 2)

    def gross_profit(self):
        '''
        毛利
        '''
        return self.total_price * self.gross_profit_rate
    def smart_gross_profit(self):
        return round(self.gross_profit(), 2)

    def tax(self):
        '''
        税费
        '''
        return self.total_price * self.tax_rate
    def smart_tax(self):
        return round(self.tax(), 2)

    def net_rate(self):
        '''
        净利率
        '''
        return self.gross_profit_rate - self.tax_rate

    def net(self):
        '''
        净利
        '''
        return self.total_price * self.net_rate()
    def smart_net(self):
        return round(self.net(), 2)

    def percentage(self):
        '''
        提成
        '''
        return self.net() * self.percentage_rate
    def smart_percentage(self):
        return round(self.percentage(), 2)

    def net_income_rate(self):
        '''
        净收入比率
        '''
        return 1 - self.percentage_rate

    def net_income(self):
        '''
        净收入
        '''
        return self.net() * self.net_income_rate()
    def smart_net_income(self):
        return round(self.net_income(), 2)













