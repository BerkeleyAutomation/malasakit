from django.conf.urls import url

from . import views

app_name = 'pcari'
urlpatterns = [ 
    url(r'^$', views.landing, name='landing'),
    url(r'^questions/$', views.create_user, name='create_user'),
    url(r'^questions/(?P<is_new>[0-9]+)/$', views.create_user, name='create_user'),
    url(r'^comparison/(?P<qid>[0-9]+)/$', views.rate, name='rate'),
    url(r'^review/$', views.review, name='review'),
    url(r'^peerevaluation/$', views.bloom, name='bloom'),
    url(r'^rate/(?P<cid>[0-9]+)/$', views.get_comment, name='get_comment'),
    url(r'^bloom/(?P<cid>[0-9]+)/$', views.rate_comment, name='rate_comment'),
    url(r'^comment/$', views.comment, name='comment'),
    url(r'^help/$', views.help, name='help'),
    url(r'^switch/$', views.switch_language, name='switch_language'),
    url(r'^personal/$', views.switch_language, name='personal'),
    url(r'^about/$', views.about, name='about'),
    url(r'^logout/$', views.logout_view, name='logout')
]
