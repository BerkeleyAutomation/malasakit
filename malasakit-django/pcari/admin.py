"""
This module defines how Django should render the admin panel.
"""

from urllib import urlencode

from django.shortcuts import redirect, reverse, render
from django.views.decorators.http import require_POST
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from .models import QualitativeQuestion, QuantitativeQuestion
from .models import CommentRating, Comment
from .models import QuantitativeQuestionRating, Respondent
from .models import History
from .models import get_direct_fields


class MalasakitAdminSite(admin.AdminSite):
    site_header = site_title = 'Malasakit'

    def get_urls(self):
        urls = super(MalasakitAdminSite, self).get_urls()
        urls += [
            url(r'^configuration/$', self.admin_view(self.configuration),
                name='configuration'),
            url(r'^analytics/$', self.admin_view(self.analytics),
                name='analytics'),
            url(r'^change-bloom-icon/$', self.admin_view(require_POST(self.change_bloom_icon)),
                name='change-bloom-icon'),
        ]
        return urls

    def configuration(self, request):
        return render(request, 'admin/configuration.html', self.each_context(request))

    def analytics(self, request):
        return render(request, 'admin/analytics.html', self.each_context(request))

    def change_bloom_icon(self, request):
        return redirect(reverse('admin:configuration'))

# pylint: disable=invalid-name
site = MalasakitAdminSite()
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)


class HistoryAdmin(admin.ModelAdmin):
    """
    Abstract admin class that defines special behavior for `History` models.
    """
    save_as_continue = False

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


class ResponseAdmin(HistoryAdmin):
    """
    Abstract admin class for `CommentRatingAdmin`, `CommentAdmin`, and
    `QuantitativeQuestionRatingAdmin`.
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
    Customizes admin change page function for `CommentRating`s.
    """
    def get_comment_message(self, comment_rating):
        # pylint: disable=no-self-use
        return comment_rating.comment.message
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
    search_fields = ('score_history_text', 'comment__message')


@admin.register(Comment, site=site)
class CommentAdmin(ResponseAdmin):
    """
    Customizes admin change page functionality for `Comment`s.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'message', 'timestamp', 'language',
                    'flagged', 'tag', 'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('message',)

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
    Customizes admin change page functionality for
    `QuantitativeQuestionRating`s.
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
    search_fields = ('question__prompt', 'score_history_text')


class QuestionAdmin(HistoryAdmin):
    """
    Abstract admin class for `QualitativeQuestionAdmin` and
    `QuantitativeQuestionAdmin`.
    """
    # Performance optimizer to limit database queries
    list_select_related = True


@admin.register(QualitativeQuestion, site=site)
class QualitativeQuestionAdmin(QuestionAdmin):
    """
    Customizes admin change page functionality for `QualitativeQuestionAdmin`.
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
    Customizes admin change page functionality for `QuantitativeQuestionAdmin`.
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
    Customizes admin change page functionality for `RespondentAdmin`.
    """
    def comments_made(self, respondent):
        # pylint: disable=no-self-use
        comments = list(respondent.comments_made)
        return '(No comments)' if not comments else ''.join(map(str, comments))

    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '(Empty)'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('id', 'comments_made', 'age', 'gender', 'location', 'language',
                    'submitted_personal_data', 'completed_survey',
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
    primary_keys = ','.join(map(str, queryset.values_list('pk', flat=True)))
    parameters = {
        'model': queryset.model.__name__,
        'format': 'csv',
        'keys': primary_keys,
    }

    url = reverse('export-data') + '?' + urlencode(parameters)
    return redirect(url)

export_selected_as_csv.short_description = 'Export selected rows as CSV'
site.add_action(export_selected_as_csv)


def export_selected_as_xlsx(modeladmin, request, queryset):
    """ Export the selected model instances as an Excel spreadsheet. """
    # pylint: disable=unused-argument
    primary_keys = ','.join(map(str, queryset.values_list('pk', flat=True)))
    parameters = {
        'model': queryset.model.__name__,
        'format': 'xlsx',
        'keys': primary_keys,
    }

    url = reverse('export-data') + '?' + urlencode(parameters)
    return redirect(url)

export_selected_as_xlsx.short_description = 'Export selected rows as an Excel spreadsheet'
site.add_action(export_selected_as_xlsx)
