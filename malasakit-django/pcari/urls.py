from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    # User-facing views
    url(r'^$', views.landing, name='landing'),
    url(r'^quantitative-questions', views.present_quantitative_questions,
        name='present-quantitative-questions'),

    # AJAX endpoints
    url(r'^save-response', views.save_response, name='save-response'),
]
