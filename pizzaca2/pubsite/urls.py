# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^ca/$', views.cas, name='cas'),
    url(r'^ca/bundle/(?P<pk>\d+)$', views.bundle,
        name='bundle'),
    url(r'^servers/$', views.servers, name='servers'),
    url(r'^identities/$', views.identities,
        name='identities'),
]
