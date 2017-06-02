from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [
    url(r'^$', views.landing, name='landing'),
    url(r'^create-user/$', views.create_user, name='create_user'),
    url(r'^create-user/(?P<is_new>[0-9]+)/$', views.create_user, name='create_user'),
    url(r'^questions/$', views.questions, name='questions'),
    url(r'^get-question-ids/$', views.get_question_ids, name='get_question_ids'),
    url(r'^get-question/(?P<qid>\d+)/$', views.get_question, name='get_question'),
    url(r'^save-answer/$', views.save_answer, name='save_answer'),
    url(r'^review/$', views.review, name='review'),
    url(r'^peerevaluation/$', views.bloom, name='bloom'),
    url(r'^rate/(?P<cid>[0-9]+)/$', views.get_comment, name='get_comment'),
    url(r'^bloom/(?P<cid>[0-9]+)/$', views.rate_comment, name='rate_comment'),
    url(r'^comment/$', views.comment, name='comment'),
    url(r'^help/$', views.help, name='help'),
    url(r'^switch/$', views.switch_language, name='switch_language'),
    url(r'^personal/$', views.switch_language, name='personal'),
    url(r'^about/$', views.about, name='about'),
    url(r'^logout/$', views.logout_view, name='logout'),

    url(r'^get-quantitative-questions', views.get_quantitative_questions, name='get-quantitative-questions'),
]
