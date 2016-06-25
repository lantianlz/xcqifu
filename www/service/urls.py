# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns('www.company.views',

                       url(r'^$', 'index'),
                       url(r'^(?P<company_id>\d+)/orders$', 'orders'),
                       url(r'^(?P<company_id>\d+)/meal$', 'meal'),
                       url(r'^(?P<company_id>\d+)/deposit$', 'deposit'),
                       url(r'^(?P<company_id>\d+)/record$', 'record'),
                       url(r'^(?P<company_id>\d+)/feedback$', 'feedback'),
                       url(r'^(?P<company_id>\d+)/product_list$', 'product_list'),
                       url(r'^(?P<company_id>\d+)/list_orders$', 'list_orders'),

                       url(r'^success$', 'success'),
                       url(r'^error$', 'error'),
                       )
