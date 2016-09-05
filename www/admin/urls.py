# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
# from django.conf import settings

urlpatterns = patterns('www.admin.views',
                       url(r'^$', 'home'),
                       url(r'^nav$', 'nav'),
                       )

# 注册用户管理
urlpatterns += patterns('www.admin.views_user',

                        url(r'^user/change_pwd$', 'change_pwd'),
                        url(r'^user/add_user$', 'add_user'),
                        url(r'^user/get_user_by_nick$', 'get_user_by_nick'),
                        url(r'^user/modify_user$', 'modify_user'),
                        url(r'^user/get_user_by_id$', 'get_user_by_id'),
                        url(r'^user/search$', 'search'),
                        url(r'^user$', 'user'),
                        )

# 用户认证管理
urlpatterns += patterns('www.admin.views_verify_info',

                        url(r'^verify_info/modify_info$', 'modify_info'),
                        url(r'^verify_info/get_info_by_id$', 'get_info_by_id'),
                        url(r'^verify_info/search$', 'search'),
                        url(r'^verify_info$', 'verify_info'),
                        )

# 类别管理
urlpatterns += patterns('www.admin.views_kind',

                        url(r'^kind/add_kind$', 'add_kind'),
                        url(r'^kind/modify_kind$', 'modify_kind'),
                        url(r'^kind/get_kind_by_id$', 'get_kind_by_id'),
                        url(r'^kind/get_kinds_by_name$', 'get_kinds_by_name'),
                        url(r'^kind/search$', 'search'),
                        url(r'^kind$', 'kind'),
                        )

# 类别开放信息
urlpatterns += patterns('www.admin.views_kind_open_info',

                        url(r'^kind_open_info/add_info$', 'add_info'),
                        url(r'^kind_open_info/remove_info$', 'remove_info'),
                        url(r'^kind_open_info/get_info_by_id$', 'get_info_by_id'),
                        url(r'^kind_open_info/search$', 'search'),
                        url(r'^kind_open_info$', 'kind_open_info'),
                        )

# 服务商管理
urlpatterns += patterns('www.admin.views_service',

                        url(r'^service/add_service$', 'add_service'),
                        url(r'^service/modify_service$', 'modify_service'),
                        url(r'^service/get_service_by_id$', 'get_service_by_id'),
                        url(r'^service/get_services_by_name$', 'get_services_by_name'),
                        url(r'^service/search$', 'search'),
                        url(r'^service$', 'service'),
                        )

# 产品管理
urlpatterns += patterns('www.admin.views_product',

                        url(r'^product/add_product$', 'add_product'),
                        url(r'^product/modify_product$', 'modify_product'),
                        url(r'^product/get_product_by_id$', 'get_product_by_id'),
                        url(r'^product/search$', 'search'),
                        url(r'^product$', 'product'),
                        )

# 预约管理
urlpatterns += patterns('www.admin.views_order',

                        url(r'^order/modify_order$', 'modify_order'),
                        url(r'^order/get_order_by_id$', 'get_order_by_id'),
                        url(r'^order/search$', 'search'),
                        url(r'^order$', 'order'),
                        )

# 个人二维码管理
urlpatterns += patterns('www.admin.views_person_qrcode',

                        url(r'^person_qrcode/search$', 'search'),
                        url(r'^person_qrcode$', 'person_qrcode'),
                        )

# 渠道二维码管理
urlpatterns += patterns('www.admin.views_channel_qrcode',

                        url(r'^channel_qrcode/add_code$', 'add_code'),
                        url(r'^channel_qrcode/modify_code$', 'modify_code'),
                        url(r'^channel_qrcode/get_code_by_id$', 'get_code_by_id'),
                        url(r'^channel_qrcode/search$', 'search'),
                        url(r'^channel_qrcode$', 'channel_qrcode'),
                        )

# 邀请人管理
urlpatterns += patterns('www.admin.views_invite',

                        url(r'^invite/search$', 'search'),
                        url(r'^invite$', 'invite'),
                        )

# 邀请人管理
urlpatterns += patterns('www.admin.views_statistics',

                        url(r'^statistics_activity/get_active_user$', 'get_active_user'),
                        url(r'^statistics_activity$', 'statistics_activity'),
                        )

# 城市
urlpatterns += patterns('www.admin.views_city',

                        url(r'^city/get_citys_by_name$', 'get_citys_by_name'),
                        url(r'^city/get_districts_by_city$', 'get_districts_by_city'),
                        url(r'^city/modify_note$', 'modify_note'),
                        url(r'^city/modify_city$', 'modify_city'),
                        url(r'^city/get_city_by_id$', 'get_city_by_id'),
                        url(r'^city/search$', 'search'),
                        url(r'^city$', 'city'),
                        )

# 缓存管理
urlpatterns += patterns('www.admin.views_caches',

                        url(r'^caches/get_cache$', 'get_cache'),
                        url(r'^caches/remove_cache$', 'remove_cache'),
                        url(r'^caches/modify_cache$', 'modify_cache'),
                        url(r'^caches$', 'caches'),
                        )

# 敏感操作日志管理
urlpatterns += patterns('www.admin.views_sensitive_operation_log',

                        url(r'^sensitive_operation_log/get_sensitive_operation_log$', 'get_sensitive_operation_log'),
                        url(r'^sensitive_operation_log$', 'sensitive_operation_log'),
                        )

# 权限
urlpatterns += patterns('www.admin.views_permission',

                        url(r'^permission/cancel_admin$', 'cancel_admin'),
                        url(r'^permission/save_user_permission$', 'save_user_permission'),
                        url(r'^permission/get_user_permissions$', 'get_user_permissions'),
                        url(r'^permission/get_all_administrators$', 'get_all_administrators'),
                        url(r'^permission$', 'permission'),
                        )
