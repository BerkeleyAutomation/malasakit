from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    url(r'^$', views.landing, name='landing'),
    url(r'^quantitative_questions', views.quantitative_questions,
        name='quantitative_questions')
]
