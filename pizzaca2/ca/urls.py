# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^ca/$', views.ca_search, name='ca_search'),
    url(r'^ca/new$', views.ca_create, name='ca_create'),
    url(r'^ca/edit/(?P<pk>\d+)$', views.ca_update, name='ca_update'),
    url(r'^ca/generate/(?P<pk>\d+)$', views.ca_generate, name='ca_generate'),
    url(r'^ca/resource/(?P<pk>\d+)/(?P<res>[A-Za-z0-9\-\_]*\.((crl)|(crt)))$',
        views.ca_get_resource, name='ca_get_resource'),
    url(r'^ca/generate_crl$', views.ca_generate_crl, name='ca_generate_crl'),

    url(r'^subca/$', views.subca_search, name='subca_search'),
    url(r'^subca/new$', views.subca_create, name='subca_create'),
    url(r'^subca/edit/(?P<pk>\d+)$', views.subca_update, name='subca_update'),
    url(r'^subca/operators/(?P<pk>\d+)$', views.subca_operators,
        name='subca_operators'),
    url(r'^subca/generate/(?P<pk>\d+)$', views.subca_generate,
        name='subca_generate'),
    url(r'^subca/resource/(?P<pk>\d+)/(?P<res>[A-Za-z0-9\-\_]*\.((crl)|(crt)))$',
        views.subca_get_resource, name='subca_get_resource'),
    url(r'^subca/generate_crl$', views.subca_generate_crl,
        name='subca_generate_crl'),
]
