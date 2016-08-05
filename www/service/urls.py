# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('www.service.views',

                       url(r'^$', 'service_list'),
                       url(r'^(?P<service_id>\d+)$', 'service_detail'),
                       url(r'^(?P<service_id>\d+)/des$', 'service_des'),

                       url(r'^success$', 'success'),
                       url(r'^error$', 'error'),
                       )
