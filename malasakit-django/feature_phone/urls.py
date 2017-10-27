"""
This module defines how URLs should route to views.
"""

from __future__ import unicode_literals

from django.conf.urls import url
from django.conf import settings
from django.views.static import serve

from feature_phone import views

# pylint: disable=invalid-name
app_name = 'feature_phone'

urlpatterns = [
    # User-facing views
    url(r'landing/$', views.landing, name='landing'),
    url(r'quantitative-questions/$', views.quantitative_questions,
        name='quantitative-questions'),
]


if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
