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
    url(r'ask-quantitative-question/$', views.ask_quantitative_question,
        name='ask-quantitative-question'),
    url(r'process-quantitative-response/$', views.process_quantitative_response,
        name='process-quantitative-response'),
    url(r'download-recording/$', views.download_recording,
        name='download-recording'),
    url(r'comments/$', views.comments, name='comments'),
    url(r'play-comment/$', views.play_comment, name='play-comment'),
    url(r'process-comment-rating/$', views.process_comment_rating,
        name='process-comment-rating'),
    url(r'qualitative-questions/$', views.qualitative_questions,
        name='qualitative-questions'),
    url(r'ask-qualitative-question/$', views.ask_qualitative_question,
        name='ask-qualitative-question'),
    url(r'process-comment/$', views.process_comment, name='process-comment'),
    url(r'ask-age/$', views.ask_age, name='ask-age'),
    url(r'process-age/$', views.process_age, name='process-age'),
    url(r'ask-gender/$', views.ask_gender, name='ask-gender'),
    url(r'process-gender/$', views.process_gender, name='process-gender'),
    url(r'record-age/$', views.record_age, name='record-age'),
    url(r'record-gender/$', views.record_gender, name='record-gender'),
    url(r'end/$', views.end, name='end'),
    url(r'error/$', views.error, name='error'),
]


if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
