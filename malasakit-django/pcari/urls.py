from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    url(r'^landing', views.landing, name='landing'),
    url(r'^quantitative_questions', views.quantitative_questions,
        name='quantitative_questions'),
    url(r'^rate_suggestions', views.rate_suggestions, name='rate_suggestions'),
    url(r'^end', views.end, name='end')
]
