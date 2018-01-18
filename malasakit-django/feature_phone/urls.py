"""
This module defines how URLs should route to views.
"""

from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url
from django.views.static import serve

from feature_phone import views

# pylint: disable=invalid-name
app_name = 'feature-phone'

urlpatterns = [
    url(r'^language/prompt/$', views.PromptLanguageView.as_view(), name='prompt-language'),
    url(r'^language/save/$', views.SaveLanguageView.as_view(), name='save-language'),
    url(r'^irb-notice/prompt/$', views.PromptIRBNoticeView.as_view(), name='prompt-irb-notice'),
    url(r'^irb-notice/save/$', views.VerifyIRBNoticeView.as_view(), name='verify-irb-notice'),
    url(r'^gender/prompt/$', views.PromptGenderView.as_view(), name='prompt-gender'),
    url(r'^gender/save/$', views.SaveGenderView.as_view(), name='save-gender'),
    url(r'^age/prompt/$', views.PromptAgeView.as_view(), name='prompt-age'),
    url(r'^age/download/$', views.download_age_recording, name='download-age'),
    url(r'^barangay/prompt/$', views.PromptBarangayView.as_view(), name='prompt-barangay'),
    url(r'^barangay/download/$', views.download_barangay_recording, name='download-barangay'),
    url(r'^quantitative-questions/instructions/$',
        views.QuantiativeQuestionInstructionsView.as_view(),
        name='quantitative-question-instructions'),
    url(r'^quantitative-questions/prompt/$', views.PromptQuantitativeQuestionView.as_view(),
        name='prompt-quantitative-question'),
    url(r'^quantitative-questions/save/$', views.SaveQuantitativeRatingView.as_view(),
        name='save-quantitative-rating'),
    url(r'^comments/instructions/$', views.CommentRatingInstructions.as_view(),
        name='comment-rating-instructions'),
    url(r'^comments/prompt/$', views.PromptCommentView.as_view(), name='prompt-comment'),
    url(r'^comments/save/$', views.SaveCommentRatingView.as_view(), name='save-comment-rating'),
    url(r'^qualitative-question/instructions/$',
        views.QualitativeQuestionInstructionsView.as_view(),
        name='qualitative-question-instructions'),
    url(r'^qualitative-questions/prompt/$', views.PromptQualitativeQuestionView.as_view(),
        name='prompt-qualitative-question'),
    url(r'^qualitative-questions/confirm/$', views.ConfirmCommentView.as_view(),
        name='confirm-comment'),
    url(r'^qualitative-questions/save/$', views.SaveCommentView.as_view(),
        name='save-comment'),
    url(r'end/$', views.end, name='end'),
    url(r'^error/$', views.error, name='error'),
    url(r'^download-recording/$', views.download_recording, name='download-recording'),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
