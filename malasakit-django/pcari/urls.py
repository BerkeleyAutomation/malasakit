from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    # User-facing views
    url(r'^$', views.index, name='index'),
    url(r'^landing', views.landing, name='landing'),
    url(r'^quantitative_questions', views.quantitative_questions,
        name='quantitative_questions'),
    url(r'^rate_suggestions', views.rate_suggestions, name='rate_suggestions'),
    url(r'^end', views.end, name='end'),

    # AJAX endpoints
    url(r'^save-response', views.save_response, name='save-response'),
]
