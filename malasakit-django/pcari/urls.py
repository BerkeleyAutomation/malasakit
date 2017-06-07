from django.conf.urls import url
from django.conf.urls.static import static

from . import views

import os

app_name = 'pcari'
urlpatterns = [
    url(r'^landing', views.landing, name='landing'),
    url(r'^quantitative_questions', views.quantitative_questions,
        name='quantitative_questions'),
    url(r'^rate_suggestions', views.rate_suggestions, name='rate_suggestions'),
    url(r'^end', views.end, name='end')
] + static('/', document_root=os.path.join(os.getcwd(), 'pcari'))
