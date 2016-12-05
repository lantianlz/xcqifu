# -*- coding: utf-8 -*-

'''
全局常量维护
'''

G_DICT_ERROR = {
    99600: u'不存在的用户',
    99601: u'找不到对象',
    99700: u'权限不足',
    99800: u'参数缺失',
    99801: u'参数异常',
    99802: u'参数重复',
    99900: u'系统错误',
    0: u'成功'
}


PERMISSIONS = [
    {'code': 'user_manage', 'name': u'用户管理', 'parent': None},
    {'code': 'add_user', 'name': u'添加用户', 'parent': 'user_manage'},
    {'code': 'query_user', 'name': u'查询用户', 'parent': 'user_manage'},
    {'code': 'modify_user', 'name': u'修改用户', 'parent': 'user_manage'},
    {'code': 'remove_user', 'name': u'删除用户', 'parent': 'user_manage'},
    {'code': 'change_pwd', 'name': u'修改用户密码', 'parent': 'user_manage'},

    {'code': 'verify_user_manage', 'name': u'用户认证管理', 'parent': None},
    {'code': 'add_verify_user', 'name': u'添加用户认证', 'parent': 'verify_user_manage'},
    {'code': 'query_verify_user', 'name': u'查询用户认证', 'parent': 'verify_user_manage'},
    {'code': 'modify_verify_user', 'name': u'修改用户认证', 'parent': 'verify_user_manage'},

    {'code': 'company_manage', 'name': u'公司管理', 'parent': None},
    {'code': 'add_company', 'name': u'添加公司', 'parent': 'company_manage'},
    {'code': 'query_company', 'name': u'查询公司', 'parent': 'company_manage'},
    {'code': 'modify_company', 'name': u'修改公司', 'parent': 'company_manage'},

    {'code': 'company_manager_manage', 'name': u'公司管理员管理', 'parent': None},
    {'code': 'add_company_manager', 'name': u'添加公司管理员', 'parent': 'company_manager_manage'},
    {'code': 'query_company_manager', 'name': u'查询公司管理员', 'parent': 'company_manager_manage'},
    {'code': 'modify_company_manager', 'name': u'修改公司管理员', 'parent': 'company_manager_manage'},
    {'code': 'remove_company_manager', 'name': u'删除公司管理员', 'parent': 'company_manager_manage'},

    {'code': 'cash_account_manage', 'name': u'现金账户管理', 'parent': None},
    {'code': 'query_cash_account', 'name': u'查询现金账户', 'parent': 'cash_account_manage'},
    {'code': 'modify_cash_account', 'name': u'修改现金账户', 'parent': 'cash_account_manage'},

    {'code': 'cash_record_manage', 'name': u'现金流水管理', 'parent': None},
    {'code': 'add_cash_record', 'name': u'添加现金流水', 'parent': 'cash_record_manage'},
    {'code': 'query_cash_record', 'name': u'查询现金流水', 'parent': 'cash_record_manage'},
    {'code': 'modify_cash_record', 'name': u'修改现金流水', 'parent': 'cash_record_manage'},

    {'code': 'kind_manage', 'name': u'类别管理', 'parent': None},
    {'code': 'add_kind', 'name': u'添加类别', 'parent': 'kind_manage'},
    {'code': 'query_kind', 'name': u'查询类别', 'parent': 'kind_manage'},
    {'code': 'modify_kind', 'name': u'修改类别', 'parent': 'kind_manage'},

    {'code': 'kind_open_info_manage', 'name': u'类别开放信息管理', 'parent': None},
    {'code': 'add_kind_open_info', 'name': u'添加类别开放信息', 'parent': 'kind_open_info_manage'},
    {'code': 'query_kind_open_info', 'name': u'查询类别开放信息', 'parent': 'kind_open_info_manage'},
    {'code': 'remove_kind_open_info', 'name': u'删除类别开放信息', 'parent': 'kind_open_info_manage'},

    {'code': 'service_manage', 'name': u'服务商管理', 'parent': None},
    {'code': 'add_service', 'name': u'添加服务商', 'parent': 'service_manage'},
    {'code': 'query_service', 'name': u'查询服务商', 'parent': 'service_manage'},
    {'code': 'modify_service', 'name': u'修改服务商', 'parent': 'service_manage'},

    {'code': 'service_cash_account_manage', 'name': u'服务商现金账户管理', 'parent': None},
    {'code': 'query_service_cash_account', 'name': u'查询服务商现金账户', 'parent': 'service_cash_account_manage'},

    {'code': 'service_cash_record_manage', 'name': u'服务商现金流水管理', 'parent': None},
    {'code': 'add_service_cash_record', 'name': u'添加服务商现金流水', 'parent': 'service_cash_record_manage'},
    {'code': 'query_service_cash_record', 'name': u'查询服务商现金流水', 'parent': 'service_cash_record_manage'},

    {'code': 'product_manage', 'name': u'产品管理', 'parent': None},
    {'code': 'add_product', 'name': u'添加产品', 'parent': 'product_manage'},
    {'code': 'query_product', 'name': u'查询产品', 'parent': 'product_manage'},
    {'code': 'modify_product', 'name': u'修改产品', 'parent': 'product_manage'},

    {'code': 'order_record_manage', 'name': u'订单管理', 'parent': None},
    {'code': 'add_order_record', 'name': u'添加订单', 'parent': 'order_record_manage'},
    {'code': 'query_order_record', 'name': u'查询订单', 'parent': 'order_record_manage'},
    {'code': 'modify_order_record', 'name': u'修改订单', 'parent': 'order_record_manage'},

    {'code': 'order_manage', 'name': u'预约管理', 'parent': None},
    {'code': 'add_order', 'name': u'添加预约', 'parent': 'order_manage'},
    {'code': 'query_order', 'name': u'查询预约', 'parent': 'order_manage'},
    {'code': 'modify_order', 'name': u'修改预约', 'parent': 'order_manage'},

    {'code': 'invite_manage', 'name': u'邀请管理', 'parent': None},
    {'code': 'query_person_qrcode', 'name': u'查询个人二维码', 'parent': 'invite_manage'},
    {'code': 'query_channel_qrcode', 'name': u'查询渠道二维码', 'parent': 'invite_manage'},
    {'code': 'add_channel_qrcode', 'name': u'添加渠道二维码', 'parent': 'invite_manage'},
    {'code': 'modify_channel_qrcode', 'name': u'修改渠道二维码', 'parent': 'invite_manage'},
    {'code': 'query_invite', 'name': u'查询邀请人', 'parent': 'invite_manage'},

    {'code': 'statistics_manage', 'name': u'统计管理', 'parent': None},
    {'code': 'get_active_user', 'name': u'活跃用户列表', 'parent': 'statistics_manage'},

    {'code': 'city_manage', 'name': u'城市管理', 'parent': None},
    #{'code': 'add_city', 'name': u'添加城市', 'parent': 'city_manage'},
    {'code': 'query_city', 'name': u'查询城市', 'parent': 'city_manage'},
    {'code': 'modify_city', 'name': u'修改城市', 'parent': 'city_manage'},

    {'code': 'tools', 'name': u'常用工具', 'parent': None},
    {'code': 'get_cache', 'name': u'查询缓存', 'parent': 'tools'},
    {'code': 'remove_cache', 'name': u'删除缓存', 'parent': 'tools'},
    {'code': 'modify_cache', 'name': u'修改缓存', 'parent': 'tools'},
    {'code': 'query_sensitive_operation_log', 'name': u'查询敏感操作日志', 'parent': 'tools'},

    {'code': 'permission_manage', 'name': u'权限管理', 'parent': None},
    {'code': 'add_user_permission', 'name': u'添加用户权限', 'parent': 'permission_manage'},
    {'code': 'query_user_permission', 'name': u'查询用户权限', 'parent': 'permission_manage'},
    {'code': 'modify_user_permission', 'name': u'修改用户权限', 'parent': 'permission_manage'},
    {'code': 'cancel_admin', 'name': u'取消管理员', 'parent': 'permission_manage'},
]
