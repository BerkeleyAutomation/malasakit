from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    url(r'^$', views.landing, name='landing'),
    url(r'^get/quantitative-questions', views.get_quantitative_questions,
        name='get-quantitative-questions'),
    url(r'^get/qualitative-questions', views.get_qualitative_questions,
        name='get-quantitative-questions'),
]
