# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^identity/$', views.identity_search, name='identity_search'),
    url(r'^identity/new$', views.identity_create, name='identity_create'),
    url(r'^identity/edit/(?P<pk>\d+)$', views.identity_update,
        name='identity_update'),
    url(r'^identity/delete$', views.identity_delete, name='identity_delete'),
    url(r'^identity/generate/(?P<pk>\d+)$',
        views.identity_generate, name='identity_generate'),
    url(r'^identity/download/p12$', views.download_p12, name='download_p12'),
    url(r'^identity/download/pem/(?P<pk>\d+)$',
        views.download_id_pem, name='download_id_pem'),
    url(r'^identity/revoke$', views.identity_revoke, name='identity_revoke'),

    url(r'^server/$', views.server_search, name='server_search'),
    url(r'^server/new$', views.server_create, name='server_create'),
    url(r'^server/edit/(?P<pk>\d+)$', views.server_update,
        name='server_update'),
    url(r'^server/delete$', views.server_delete, name='server_delete'),
    url(r'^server/generate/(?P<pk>\d+)$', views.server_generate,
        name='server_generate'),
    url(r'^server/download/pem/(?P<pk>\d+)$',
        views.download_srv_pem, name='download_srv_pem'),
    url(r'^server/revoke$', views.server_revoke, name='server_revoke'),
]
