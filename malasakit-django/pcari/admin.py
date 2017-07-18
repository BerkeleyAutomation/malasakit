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
import math
import os

from django.conf import settings
from django.shortcuts import redirect, reverse, render
from django.views.decorators.http import require_POST
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from pcari.models import QualitativeQuestion, QuantitativeQuestion
from pcari.models import CommentRating, Comment
from pcari.models import QuantitativeQuestionRating, Respondent
from pcari.models import History
from pcari.models import get_direct_fields
from pcari.views import export_data

__all__ = [
    'MalasakitAdminSite',
    'HistoryAdmin',
    'QuestionAdmin',
    'ResponseAdmin',
    'QuantitativeQuestionAdmin',
    'QuantitativeQuestionRatingAdmin',
    'QualitativeQuestionAdmin',
    'CommentAdmin',
    'CommentRatingAdmin',
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

    def change_bloom_icon(self, request):
        """ Save an image file of a custom bloom icon. """
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
site.register(Group, GroupAdmin)
site.filter_actions(User, ['delete_selected'])
site.filter_actions(Group, ['delete_selected'])


class HistoryAdmin(admin.ModelAdmin):
    """
    Base admin behavior that defines special functionality for
    :class:`pcari.models.History` models.
    """
    save_as_continue = False

    actions = ('mark_active', 'mark_inactive')

    def save_model(self, request, obj, form, change):
        if change and issubclass(obj.__class__, History):
            old_instance = obj.__class__.objects.get(id=obj.id)
            if set(obj.diff(old_instance)) - {'active'}:
                obj = obj.make_copy()
                obj.predecessor = old_instance
                old_instance.active, obj.active = False, True
                old_instance.save()
        super(HistoryAdmin, self).save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        model = obj.__class__
        if obj and issubclass(model, History) and not obj.active:
            field_names = [field.name for field in get_direct_fields(model)]
            field_names.remove('active')
            return field_names
        return self.readonly_fields + ('predecessor', )

    def mark_active(self, request, queryset):
        """ Mark selected instances as active in bulk. """
        num_marked = queryset.update(active=True)
        message = '{0} row{1} successfully marked as active.'
        message = message.format(num_marked, 's' if num_marked != 1 else '')
        self.message_user(request, message)

    def mark_inactive(self, request, queryset):
        """ Mark selected instances as inactive in bulk. """
        num_marked = queryset.update(active=False)
        message = '{0} row{1} successfully marked as inactive.'
        message = message.format(num_marked, 's' if num_marked != 1 else '')
        self.message_user(request, message)


class ResponseAdmin(HistoryAdmin):
    """
    Base admin behavior for :class:`pcari.models.Response` models.
    """
    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '-- Empty response --'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Sets default ordering to be most recent comment first
    ordering = ('-timestamp',)


@admin.register(CommentRating, site=site)
class CommentRatingAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.CommentRating`.
    """
    def get_comment_message(self, comment_rating):
        message = comment_rating.comment.message
        return message if message.strip() else self.empty_value_display
    get_comment_message.short_description = 'Comment message'

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_comment_message', 'score', 'timestamp',
                    'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_comment_message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'active')

    # Sets fields as readonly
    readonly_fields = ('timestamp', )

    # Enables search
    search_fields = ('score', 'comment__message')


@admin.register(Comment, site=site)
class CommentAdmin(ResponseAdmin):
    """
    Admin behavior for :class:`pcari.models.Comment`.
    """
    def display_message(self, comment):
        return comment.message if comment.message.strip() else self.empty_value_display
    display_message.short_description = 'Message'

    def display_mean_score(self, comment):
        # pylint: disable=no-self-use
        mean_score = comment.mean_score
        return str(round(mean_score, 3)) if not math.isnan(mean_score) else '(No ratings)'
    display_mean_score.short_description = 'Mean score'

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'display_message', 'timestamp', 'language',
                    'flagged', 'tag', 'active', 'display_mean_score',
                    'num_ratings')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('display_message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'language', 'flagged', 'tag', 'active')

    # Enables search
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
    def get_question_prompt(self, question_rating):
        # pylint: disable=no-self-use
        return question_rating.question.prompt
    get_question_prompt.short_description = 'Question prompt'

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_question_prompt', 'timestamp', 'score',
                    'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_question_prompt',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'active')

    # Sets fields as readonly
    readonly_fields = ('timestamp', )

    # Enables search
    search_fields = ('question__prompt', 'score')


class QuestionAdmin(HistoryAdmin):
    """
    Base admin behavior for :class:`pcari.models.Question` models.
    """
    list_select_related = True
    """ bool: Performance optimizer to limit database queries. """


@admin.register(QualitativeQuestion, site=site)
class QualitativeQuestionAdmin(QuestionAdmin):
    """
    Admin behavior for :class:`pcari.models.QualitativeQuestion`.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('prompt', 'tag', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('prompt', 'tag', 'active')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(QuantitativeQuestion, site=site)
class QuantitativeQuestionAdmin(QuestionAdmin):
    """
    Admin behavior for :class:`pcari.models.QuantitativeQuestion`.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('prompt', 'tag', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('tag', 'active')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(Respondent, site=site)
class RespondentAdmin(HistoryAdmin):
    """
    Admin behavior for :class:`pcari.models.Respondent`.
    """
    def display_location(self, respondent):
        return respondent.location if respondent.location.strip() else self.empty_value_display
    display_location.short_description = 'Location'

    def comments_made(self, respondent):
        # pylint: disable=no-self-use
        comments = list(respondent.comments)
        return '(No comments)' if not comments else ''.join(map(str, comments))

    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '(Empty)'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('id', 'comments_made', 'age', 'gender', 'display_location',
                    'language', 'submitted_personal_data', 'completed_survey',
                    'num_questions_rated', 'num_comments_rated', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('gender', 'language', 'submitted_personal_data',
                   'completed_survey', 'active')

    # Enables search
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
