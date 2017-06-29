"""
This module defines how URLs should route to views.
"""

from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

# pylint: disable=invalid-name
app_name = 'pcari'

urlpatterns = [
    # User-facing views
    url(r'^$', views.index, name='index'),
    url(r'^landing/$', views.landing, name='landing'),
    url(r'^quantitative-questions/$', views.quantitative_questions,
        name='quantitative-questions'),
    url(r'^peer-responses/$', views.peer_responses, name='peer-responses'),
    url(r'^rate-comments/$', views.rate_comments, name='rate-comments'),
    url(r'^qualitative-questions/$', views.qualitative_questions,
        name='qualitative-questions'),
    url(r'^personal-information/$', views.personal_information,
        name='personal-information'),
    url(r'^end/$', views.end, name='end'),

    # ServiceWorker script- special case
    url(r'^sw.js$',
        TemplateView.as_view(template_name='sw.js',
                             content_type='application/javascript'),
        name='sw.js'),
]

ajax_urlpatterns = [
    url(r'^fetch-comments/$', views.fetch_comments, name='fetch-comments'),
    url(r'^fetch-qualitative-questions/$', views.fetch_qualitative_questions,
        name='fetch-qualitative-questions'),
    url(r'^save-response/$', views.save_response, name='save-response'),
    url(r'^export-data/$', views.export_data, name='export-data'),
    url(r'^fetch-location-data/$', views.fetch_location_data,
        name='fetch-location-data'),
]
