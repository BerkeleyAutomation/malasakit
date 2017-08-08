"""
This module defines how URLs should route to views.
"""

from __future__ import unicode_literals

from django.conf.urls import url

from feature_phone import views

# pylint: disable=invalid-name
app_name = 'feature_phone'

urlpatterns = [
    # User-facing views
    url(r'landing/$', views.landing, name='landing'),
    url(r'quantitative-questions/$', views.quantitative_questions,
        name="quantitative-questions"),
    url(r'rate-comments/$', views.rate_comments, name='rate-comments'),
    url(r'end/$', views.end, name='end'),
]
