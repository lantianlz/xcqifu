# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('',
                       url(r'^login_weixin$', 'www.account.views.login_weixin'),
                       url(r'^login$', 'www.account.views.login'),
                       url(r'^get_weixin_login_state$', 'www.account.views.get_weixin_login_state'),
                       url(r'^logout$', 'www.account.views.logout'),
                       url(r'^qiniu_img_return$', 'www.misc.views.qiniu_img_return'),
                       url(r'^save_img$', 'www.misc.views.save_img'),
                       url(r'^crop_img$', 'www.misc.views.crop_img'),
                       url(r'^qrcode$', 'www.misc.views.qrcode'),
                       url(r'^customers$', 'www.company.views.customers'),
                       url(r'^product_list$', 'www.company.views.anonymous_product_list'),
                       url(r'^fruit_price$', 'www.company.views.anonymous_fruit_price'),

                       url(r'^$', 'www.account.views.home_welcome'),
                       url(r'^admin/', include('www.admin.urls')),
                       url(r'^account/', include('www.account.urls')),
                       url(r'^weixin/', include('www.weixin.urls')),

                       url(r'^(?P<txt_file_name>\w+)\.txt$', 'www.misc.views.txt_view'),
                       url(r'^s/(?P<template_name>.*)$', 'www.misc.views.static_view'),
                       url(r'^500$', 'www.misc.views.test500'),
                       url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),
                       url(r'^crossdomain.xml$', direct_to_template, {'template': 'crossdomain.xml'}),
                       )

urlpatterns += patterns('misc.views_paycallback',
                        (r'^alipaycallback$', 'alipaycallback'),
                        (r'^alipaynotify$', 'alipaynotify'),
                        (r'^weixinnotify$', 'weixinnotify'),
                        (r'^weixin_success_info$', 'weixin_success_info'),
                        (r'^weixinwarning$', 'weixinwarning'),

                        (r'^test_paycallback$', 'test_paycallback'),
                        )
