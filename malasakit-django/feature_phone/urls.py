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
        name="quantitative-questions"),
    url(r'rate-comments/([0-9])/$', views.rate_comments, name='rate-comments'),
    url(r'qualitative-questions/$', views.qualitative_questions,
        name="qualitative-questions"),
    url(r'process-recording/(.+)/', views.process_recording,
        name="process-recording"),
    url(r'end/$', views.end, name='end'),
]


if settings.DEBUG:
    print settings.MEDIA_ROOT
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
