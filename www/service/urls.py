# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('www.service.views',

                       url(r'^$', 'service_list'),
                       url(r'^(?P<service_id>\d+)$', 'service_detail'),
                       url(r'^product/(?P<product_id>\d+)$', 'product_detail'),
                       url(r'^my_order$', 'my_order'),
                       url(r'^success$', 'success'),
                       url(r'^error$', 'error'),
                       )
