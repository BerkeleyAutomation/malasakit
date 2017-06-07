"""
This module defines how URLs should route to views.
"""

from django.conf.urls import url

from . import views

# pylint: disable=invalid-name
app_name = 'pcari'
urlpatterns = [
    # User-facing views
    url(r'^$', views.index, name='index'),
    url(r'^landing/$', views.landing, name='landing'),
    url(r'^personal-information/$', views.personal_information,
        name='personal-information'),
    url(r'^quantitative-questions/$', views.quantitative_questions,
        name='quantitative-questions'),
    url(r'^response-histograms/$', views.response_histograms,
        name='response-histograms'),
    url(r'^rate-comments/$', views.rate_comments, name='rate-comments'),
    url(r'^qualitative-questions/$', views.qualitative_questions,
        name='qualitative-questions'),
    url(r'^end/$', views.end, name='end'),

    # AJAX endpoints
    url(r'^save-response', views.save_response, name='save-response'),
]
