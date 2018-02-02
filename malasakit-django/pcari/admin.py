"""
This module defines how Django should render the admin panel.

References:
  * `Django Admin Site Reference <https://docs.djangoproject.com/en/dev/ref/contrib/admin/>`_
  * `Django Admin Actions <https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/>`_
"""

from __future__ import unicode_literals
from base64 import b64encode
from collections import OrderedDict
import json
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import redirect, reverse, render
from django.views.decorators.http import require_POST
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType

from pcari.models import QualitativeQuestion, Comment, CommentRating
from pcari.models import OptionQuestion, OptionQuestionChoice
from pcari.models import QuantitativeQuestionRating, QuantitativeQuestion
from pcari.models import Location, Respondent
from pcari.views import export_data, translate
from feature_phone import models as phone_models

__all__ = [
    'MalasakitAdminSite',
    'QuantitativeQuestionAdmin',
    'QuantitativeQuestionRatingAdmin',
    'QualitativeQuestionAdmin',
    'CommentAdmin',
    'CommentRatingAdmin',
    'OptionQuestionAdmin',
    'OptionQuestionChoiceAdmin',
    'LocationAdmin',
    'RespondentAdmin',
]


class MalasakitAdminSite(admin.AdminSite):
    """
    A custom admin site for Malasakit with augmented configuration and
    statistics functionality.
    """
    site_header = site_title = 'Malasakit'

    def get_urls(self):
        urls = super(MalasakitAdminSite, self).get_urls()
        urls += [
            url(r'^configuration/$', self.admin_view(self.configuration),
                name='configuration'),
            url(r'^statistics/$', self.admin_view(self.statistics),
                name='statistics'),
            url(r'^change-landing-image/$',
                self.admin_view(require_POST(self.change_landing_image)),
                name='change-landing-image'),
            url(r'^change-bloom-icon/$', self.admin_view(require_POST(self.change_bloom_icon)),
                name='change-bloom-icon'),
        ]
        return urls

    def configuration(self, request):
        """ Render a page for staff users to configure the application. """
        context = self.each_context(request)
        if 'messages' in request.session:
            context['messages'] = request.session['messages']
            del request.session['messages']
        return render(request, 'admin/configuration.html', context)

    def statistics(self, request):
        """ Render a statistics page. """
        return render(request, 'admin/statistics.html', self.each_context(request))

    def change_landing_image(self, request):
        """ Save an image file as the landing page image. """
        # pylint: disable=no-self-use
        uploaded_file = request.FILES['landing-image']
        img_dir = os.path.join(settings.STATIC_ROOT, 'img')
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        destination = os.path.join(img_dir, 'landing')
        default_storage.delete(destination)
        default_storage.save(destination, ContentFile(uploaded_file.read()))

        request.session['messages'] = ['Successfully changed landing image.']
        return redirect(reverse('admin:configuration'))

    def change_bloom_icon(self, request):
        """ Save an image file as a custom bloom icon. """
        # pylint: disable=no-self-use
        uploaded_file = request.FILES['bloom-icon']
        image_data = b64encode(uploaded_file.read())
        content_type = uploaded_file.content_type

        parent_dir = os.path.join(settings.STATIC_ROOT, 'data')
        if not os.path.exists(parent_dir):
            os.mkdir(parent_dir)

        path = os.path.join(parent_dir, 'bloom-icon.json')
        with open(path, 'wb+') as destination:
            obj = {
                'content-type': content_type,
                'encoded-image': image_data,
            }
            json.dump(obj, destination)

        request.session['messages'] = ['Successfully uploaded bloom icon.']
        return redirect(reverse('admin:configuration'))

    def filter_actions(self, model, action_names=None):
        """
        Restrict the actions a model admin may take.

        This restriction is accomplished by wrapping the ``get_actions`` method
        of the model admin associated with the given ``model``.

        Args:
            model: The class of the model. The model must have been registered
                with the site.
            action_names (list): A list of action names (strings) whose
                associated actions should be allowed.
        """
        if action_names is None:
            action_names = []

        model_admin = self._registry[model]
        get_actions_inner = model_admin.get_actions
        def get_actions_wrapper(request):
            actions = get_actions_inner(request)
            return OrderedDict((name, actions[name]) for name in action_names)
        model_admin.get_actions = get_actions_wrapper

# pylint: disable=invalid-name
site = MalasakitAdminSite()
site.register(User, UserAdmin)
site.filter_actions(User, ['delete_selected'])
site.register(Group, GroupAdmin)
site.filter_actions(Group, ['delete_selected'])


class ResponseAdmin(admin.ModelAdmin):
    """
    Base admin behavior for :class:`pcari.models.Response` models.
    """
    empty_value_display = '(Empty)'
    ordering = ('-timestamp',)


@admin.register(CommentRating, site=site)
class CommentRatingAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.CommentRating`.
    """
    def get_comment_message(self, rating):
        message = rating.comment.message
        return message if message.strip() else self.empty_value_display
    get_comment_message.short_description = 'Comment message'

    def get_score(self, rating):
        # pylint: disable=no-self-use
        return rating.score if rating.score is not None else '(Skipped)'
    get_score.short_description = 'Score'
    get_score.admin_order_field = 'score'

    list_display = ('respondent', 'get_comment_message', 'get_score', 'timestamp')
    list_display_links = ('get_comment_message',)
    list_filter = ('timestamp', )
    readonly_fields = ('timestamp', )
    search_fields = ('score', 'comment__message')


@admin.register(Comment, site=site)
class CommentAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.Comment`.
    """
    def display_message(self, comment):
        return comment.message.strip() or self.empty_value_display
    display_message.short_description = 'Message'

    def num_ratings(self, comment):
        # pylint: disable=no-self-use
        return comment.num_ratings
    num_ratings.short_description = 'Number of ratings'
    num_ratings.admin_order_field = 'num_ratings'

    def display_mean_score(self, comment):
        # pylint: disable=no-self-use
        mean_score = comment.mean_score
        return unicode(round(mean_score, 3)) if mean_score is not None else '(No ratings)'
    display_mean_score.short_description = 'Mean score'
    display_mean_score.admin_order_field = 'mean_score'

    def display_wilson_score(self, comment):
        # pylint: disable=no-self-use
        return unicode(round(comment.score_95ci_lower, 3))
    display_wilson_score.short_description = 'Wilson score'
    display_wilson_score.admin_order_field = 'score_95ci_lower'

    list_display = ('respondent', 'display_message', 'timestamp', 'language',
                    'flagged', 'tag', 'num_ratings',
                    'display_mean_score', 'display_wilson_score')
    list_display_links = ('display_message',)
    list_filter = ('timestamp', 'language', 'flagged', 'tag')
    search_fields = ('message', 'tag')
    actions = ('flag_comments', 'unflag_comments')

    def flag_comments(self, request, queryset):
        """
        Flag selected comments in bulk and inform the user how many were flagged.
        """
        num_flagged = queryset.update(flagged=True)
        message = '{0} comment{1} successfully flagged.'
        message = message.format(num_flagged, 's' if num_flagged != 1 else '')
        self.message_user(request, message)

    def unflag_comments(self, request, queryset):
        """
        Unflag selected comments in bulk and inform how many were unflagged.
        """
        num_unflagged = queryset.update(flagged=False)
        message = '{0} comment{1} successfully unflagged.'
        message = message.format(num_unflagged, 's' if num_unflagged != 1 else '')
        self.message_user(request, message)


@admin.register(QuantitativeQuestionRating, site=site)
class QuantitativeQuestionRatingAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.QuantitativeQuestionRating`.
    """
    def question_prompt(self, rating):
        return rating.question.prompt.strip() or self.empty_value_display

    def get_score(self, rating):
        # pylint: disable=no-self-use
        return rating.score if rating.score is not None else '(Skipped)'
    get_score.short_description = 'Score'
    get_score.admin_order_field = 'score'

    list_display = ('respondent', 'question_prompt', 'timestamp', 'get_score')
    list_display_links = ('question_prompt', )
    list_filter = ('timestamp', )
    readonly_fields = ('timestamp', )
    search_fields = ('question_prompt', 'score')


@admin.register(OptionQuestionChoice, site=site)
class OptionQuestionChoiceAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.OptionQuestionChoice`.
    """
    def question_prompt(self, choice):
        return choice.question.prompt.strip() or self.empty_value_display

    def option_display(self, choice):
        return choice.option or self.empty_value_display
    option_display.short_description = 'Option'

    list_display = ('respondent', 'question_prompt', 'timestamp', 'option_display')
    list_display_links = ('question_prompt', )
    list_filter = ('timestamp', )
    search_fields = ('question_prompt', 'option')


def export_to_feature_phone(modeladmin, request, queryset):
    """ Export the selected questions to the feature phone application. """
    # pylint: disable=unused-argument
    for question in queryset:
        for language, _ in settings.LANGUAGES:
            components = [question._meta.label_lower.replace('.', '-'),
                          unicode(question.pk), language]
            phone_models.Question.objects.get_or_create(
                key='-'.join(components),
                defaults={
                    'text': translate(question.prompt, language),
                    'language': language,
                    'related_object_type': ContentType.objects.get_for_model(question),
                    'related_object': question,
                }
            )
    message = 'Successfully copied {} question{}.'
    count = queryset.count()
    modeladmin.message_user(request, message.format(count, 's' if count > 1 else ''))
export_to_feature_phone.short_description = 'Use questions for feature phone'


@admin.register(QualitativeQuestion, site=site)
class QualitativeQuestionAdmin(admin.ModelAdmin):
    """
    Admin behavior for :class:`pcari.models.QualitativeQuestion`.
    """
    def display_question_num_comments(self, question):
        # pylint: disable=no-self-use
        return question.comments.count()
    display_question_num_comments.short_description = 'Number of comments'

    empty_value_display = '(Empty)'
    list_display = ('prompt', 'tag', 'display_question_num_comments')
    list_filter = ('tag', )
    search_fields = ('prompt', 'tag')
    actions = [export_to_feature_phone]


@admin.register(QuantitativeQuestion, site=site)
class QuantitativeQuestionAdmin(admin.ModelAdmin):
    """
    Admin behavior for :class:`pcari.models.QuantitativeQuestion`.
    """
    def num_ratings(self, comment):
        # pylint: disable=no-self-use
        return comment.num_ratings
    num_ratings.short_description = 'Number of ratings'
    num_ratings.admin_order_field = 'num_ratings'

    empty_value_display = '(Empty)'
    list_display = ('prompt', 'tag', 'num_ratings')
    list_filter = ('tag', )
    search_fields = ('prompt', 'tag')
    actions = [export_to_feature_phone]


@admin.register(OptionQuestion, site=site)
class OptionQuestionAdmin(admin.ModelAdmin):
    """
    Admin behavior for :class:`pcari.models.OptionQuestion`.
    """
    def get_prompt(self, question):
        return question.prompt.strip() or self.empty_value_display
    get_prompt.short_description = 'Prompt'

    def get_tag(self, question):
        return question.tag.strip() or self.empty_value_display
    get_tag.short_description = 'Tag'

    def options(self, option_question):
        return ', '.join(option_question.options) or self.empty_value_display

    empty_value_display = '(Empty)'
    list_display = ('get_prompt', 'options', 'get_tag')
    list_filter = ('tag', )
    search_fields = ('prompt', 'options', 'tag')


@admin.register(Location, site=site)
class LocationAdmin(admin.ModelAdmin):
    """ Admin behavior for :class:`pcari.models.Location`. """
    def display_country(self, location):
        return location.country or self.empty_value_display
    display_country.short_description = 'Country'
    display_country.admin_order_field = 'country'

    def display_province(self, location):
        return location.province or self.empty_value_display
    display_province.short_description = 'Province'
    display_province.admin_order_field = 'province'

    def display_municipality(self, location):
        return location.municipality or self.empty_value_display
    display_municipality.short_description = 'Municipality'
    display_municipality.admin_order_field = 'municipality'

    def display_division(self, location):
        return location.division or self.empty_value_display
    display_division.short_description = 'Division'
    display_division.admin_order_field = 'division'

    def enable_as_input_options(self, request, queryset):
        """ Enable locations as valid inputs in bulk. """
        num_enabled = queryset.update(enabled=True)
        message = '{0} location{1} successfully enabled as available options.'
        message = message.format(num_enabled, 's' if num_enabled != 1 else '')
        self.message_user(request, message)

    def disable_as_input_options(self, request, queryset):
        """ Disable locations as valid inputs in bulk. """
        num_disabled = queryset.update(enabled=False)
        message = '{0} location{1} successfully disabled as available options.'
        message = message.format(num_disabled, 's' if num_disabled != 1 else '')
        self.message_user(request, message)

    empty_value_display = '(Empty)'
    actions = ('enable_as_input_options', 'disable_as_input_options')
    list_display = ('id', 'display_country', 'display_province',
                    'display_municipality', 'display_division', 'enabled')
    list_filter = ('country', 'province')
    search_fields = ('id', 'country', 'province', 'municipality', 'division')


@admin.register(Respondent, site=site)
class RespondentAdmin(admin.ModelAdmin):
    """
    Admin behavior for :class:`pcari.models.Respondent`.
    """
    def display_location(self, respondent):
        """ Yield a placeholder if the respondent has no known location. """
        if not respondent.location:
            return self.empty_value_display
        return respondent.location.division.strip() or self.empty_value_display
    display_location.short_description = 'Location'

    def comments(self, respondent):
        # pylint: disable=no-self-use
        comments = list(respondent.comments)
        return '(No comments)' if not comments else ''.join(map(unicode, comments))

    empty_value_display = '(Empty)'
    list_display = ('id', 'comments', 'age', 'gender', 'display_location',
                    'language', 'num_questions_rated', 'num_comments_rated')
    list_filter = ('gender', 'language')
    search_fields = ('gender', 'location', 'language',
                     'submitted_personal_data', 'completed_survey')


def export_selected_as_csv(modeladmin, request, queryset):
    """ Export the selected model instances as comma-separated values (CSV). """
    # pylint: disable=unused-argument
    return export_data(queryset, 'csv')

export_selected_as_csv.short_description = 'Export selected rows as CSV'
site.add_action(export_selected_as_csv)


def export_selected_as_xlsx(modeladmin, request, queryset):
    """ Export the selected model instances as an Excel spreadsheet. """
    # pylint: disable=unused-argument
    return export_data(queryset, 'xlsx')

export_selected_as_xlsx.short_description = 'Export selected rows as an Excel spreadsheet'
site.add_action(export_selected_as_xlsx)
