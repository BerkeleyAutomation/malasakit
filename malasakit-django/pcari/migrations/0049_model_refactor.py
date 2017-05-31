# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-30 22:03
from __future__ import unicode_literals

import json

from django.db import models, migrations, IntegrityError


LANGUAGES = (
    ('ENG', 'English'),
    ('FIL', 'Filipino')
)

GENDERS = (
    ('M', 'Male'),
    ('F', 'Female'),
)


def populate_qualitative_questions_forward(apps, schema_editor):
    QualitativeQuestion = apps.get_model('pcari', 'QualitativeQuestion')
    db_alias = schema_editor.connection.alias

    prompt = 'How could your Barangay help you better prepare for a disaster?'
    count = QualitativeQuestion.objects.using(db_alias).filter(prompt=prompt).count()
    if count == 0:
        QualitativeQuestion(prompt=prompt, tag='Preparedness Suggestion').save()
    elif count > 1:
        raise ValueError('duplicate question')


def convert_missing_age_forward(apps, schema_editor):
    UserData = apps.get_model('pcari', 'UserData')
    db_alias = schema_editor.connection.alias

    # `views.py` used an age of -1 by default, and `models.py` used 0
    # The correct value for missing data for this column is `None`
    for user_data in UserData.objects.using(db_alias).filter(age__lte=0).all():
        user_data.age = None
        user_data.save()


def populate_respondent_language_forward(apps, schema_editor):
    UserData = apps.get_model('pcari', 'UserData')
    db_alias = schema_editor.connection.alias

    for user_data in UserData.objects.using(db_alias).all():
        if user_data.language == 'Filipino':
            user_data.language = 'FIL'
        elif user_data.language == 'English':
            user_data.language = 'ENG'
        else:
            raise ValueError('invalid language choice: "{0}"'.format(user_data.language))
        user_data.save()


def populate_respondent_progress_forward(apps, schema_editor):
    UserData = apps.get_model('pcari', 'UserData')
    UserProgression = apps.get_model('pcari', 'UserProgression')
    db_alias = schema_editor.connection.alias

    for user_data in UserData.objects.using(db_alias).all():
        user_data.submitted_personal_data = True
        user_data.completed_survey = True
        user_data.save()


def populate_comment_question_forward(apps, schema_editor):
    Comment = apps.get_model('pcari', 'Comment')
    QualitativeQuestion = apps.get_model('pcari', 'QualitativeQuestion')
    db_alias = schema_editor.connection.alias

    for comment in Comment.objects.using(db_alias).all():
        comment.question = QualitativeQuestion.objects.using(db_alias).get(tag='Preparedness Suggestion')
        comment.save()


def standardize_comment_messages_forward(apps, schema_editor):
    """
    Standardize comments to hold only one translation.

    For comments with more than one translation, we store messages not in the
    original language in `comments.json`.
    """
    Comment = apps.get_model('pcari', 'Comment')
    db_alias = schema_editor.connection.alias
    translations = {}

    for comment in Comment.objects.using(db_alias).all():
        language = comment.original_language
        if language == 'Filipino':
            comment.language = 'FIL'
            comment.message = comment.filipino_comment
        elif language == 'English':
            comment.language = 'ENG'
            comment.message = comment.comment
        else:
            raise ValueError('invalid language choice: "{0}"'.format(user_data.language))
        comment.save()

        if comment.comment.strip() and comment.filipino_comment.strip():
            if comment.language == 'FIL':
                translated_comment, other_language = comment.comment, 'ENG'
            else:
                translated_comment, other_language = comment.filipino_comment, 'FIL'
            translations[comment.id] = {'language': other_language,
                                        'message': translated_comment}

    with open('comment-translations.json', 'w+') as json_file:
        json_file.write(json.dumps(translations, indent=4).encode('utf-8'))
        json_file.write('\n')


def populate_comment_respondent_forward(apps, schema_editor):
    Comment = apps.get_model('pcari', 'Comment')
    Respondent = apps.get_model('pcari', 'Respondent')
    db_alias = schema_editor.connection.alias

    for comment in Comment.objects.using(db_alias).all():
        comment.respondent = Respondent.objects.using(db_alias).get(user_id=comment.user_id)
        comment.save()


def populate_quantitative_question_ratings(apps, schema_editor):
    Rating = apps.get_model('pcari', 'Rating')
    QuantitativeQuestionRating = apps.get_model('pcari', 'QuantitativeQuestionRating')
    Respondent = apps.get_model('pcari', 'Respondent')
    QuantitativeQuestion = apps.get_model('pcari', 'QuantitativeQuestion')
    db_alias = schema_editor.connection.alias

    for rating in Rating.objects.using(db_alias).all():
        new_rating = QuantitativeQuestionRating(
            respondent=Respondent.objects.using(db_alias).get(user_id=rating.user_id),
            timestamp=rating.date,
            score=rating.score,
            question=QuantitativeQuestion.objects.using(db_alias).get(id=rating.qid),
        )
        new_rating.save()


def populate_comment_rating_respondent_forward(apps, schema_editor):
    CommentRating = apps.get_model('pcari', 'CommentRating')
    Respondent = apps.get_model('pcari', 'Respondent')
    db_alias = schema_editor.connection.alias

    for comment_rating in CommentRating.objects.using(db_alias).all():
        comment_rating.respondent = Respondent.objects.using(db_alias).get(user_id=comment_rating.user_id)
        comment_rating.save()


def populate_comment_rating_comment_forward(apps, schema_editor):
    CommentRating = apps.get_model('pcari', 'CommentRating')
    Comment = apps.get_model('pcari', 'Comment')
    db_alias = schema_editor.connection.alias

    for comment_rating in CommentRating.objects.using(db_alias).all():
        if comment_rating.cid == -1:  # The default value
            comment_rating.delete()
        else:
            try:
                comment_rating.comment = Comment.objects.get(id=comment_rating.cid)
                comment_rating.save()
            except Comment.DoesNotExist:
                comment_rating.delete()


def delete_duplicate_comment_ratings_forward(apps, schema_editor):
    CommentRating = apps.get_model('pcari', 'CommentRating')
    db_alias = schema_editor.connection.alias

    id_pairs = list(CommentRating.objects.using(db_alias).values_list('respondent_id', 'comment_id'))
    duplicate_id_pairs = [id_pair for id_pair in id_pairs if id_pairs.count(id_pair) > 1]

    for respondent_id, comment_id in set(duplicate_id_pairs):
        query = CommentRating.objects.using(db_alias)
        query = query.filter(respondent_id=respondent_id, comment_id=comment_id)
        assert query.count() > 1

        rating_to_keep = query.first()
        for rating in query.exclude(id=rating_to_keep.id).all():
            print('=> Deleting duplicate comment rating')
            rating.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pcari', '0048_auto_20170407_1732'),
    ]

    operations = [
        migrations.DeleteModel('GeneralSetting'),
        migrations.DeleteModel('Progression'),
        migrations.DeleteModel('FlaggedComment'),

        migrations.RenameField('QuantitativeQuestion', 'qid', 'id'),
        migrations.RenameField('QuantitativeQuestion', 'question', 'prompt'),
        migrations.AlterField('QuantitativeQuestion', 'prompt', models.TextField(blank=True)),
        migrations.RemoveField('QuantitativeQuestion', 'average_score'),
        migrations.RemoveField('QuantitativeQuestion', 'number_rated'),
        migrations.AlterField('QuantitativeQuestion', 'tag', models.CharField(max_length=64, blank=True, default='')),
        migrations.RemoveField('QuantitativeQuestion', 'filipino_tag'),
        migrations.RemoveField('QuantitativeQuestion', 'filipino_question'),

        migrations.RenameField('QualitativeQuestion', 'qid', 'id'),
        migrations.RenameField('QualitativeQuestion', 'question', 'prompt'),
        migrations.AlterField('QualitativeQuestion', 'prompt', models.TextField(blank=True)),
        migrations.RemoveField('QualitativeQuestion', 'filipino_question'),
        migrations.AddField('QualitativeQuestion', 'tag', models.CharField(max_length=64, blank=True, default='')),
        migrations.RunPython(populate_qualitative_questions_forward),

        migrations.RunPython(convert_missing_age_forward),
        migrations.AlterField('UserData', 'age',
                              models.PositiveSmallIntegerField(default=None, null=True, blank=True)),
        migrations.RenameField('UserData', 'barangay', 'location'),
        migrations.AlterField('UserData', 'location',
                              models.CharField(max_length=512, default='', blank=True)),
        migrations.AlterField('UserData', 'gender',
                              models.CharField(max_length=1, choices=GENDERS, default='', blank=True)),
        migrations.RunPython(populate_respondent_language_forward),
        migrations.AlterField('UserData', 'language', models.CharField(max_length=3, choices=LANGUAGES)),
        migrations.AddField('UserData', 'submitted_personal_data',
                            models.BooleanField(default=False)),
        migrations.AddField('UserData', 'completed_survey',
                            models.BooleanField(default=False)),
        migrations.RunPython(populate_respondent_progress_forward),
        migrations.RenameModel('UserData', 'Respondent'),
        migrations.DeleteModel('UserProgression'),

        migrations.AddField('Comment', 'question',
                            models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE, default=0), preserve_default=False),
        migrations.RunPython(populate_comment_question_forward),
        migrations.AddField('Comment', 'language',
                            models.CharField(max_length=3, choices=LANGUAGES, default='FIL'), preserve_default=False),
        migrations.AddField('Comment', 'message', models.TextField(blank=True)),
        migrations.RunPython(standardize_comment_messages_forward),
        migrations.AddField('Comment', 'respondent',
                            models.ForeignKey('Respondent', on_delete=models.CASCADE, default=0), preserve_default=False),
        migrations.RunPython(populate_comment_respondent_forward),
        migrations.AddField('Comment', 'flagged', models.BooleanField(default=False)),
        migrations.RemoveField('Comment', 'user'),
        migrations.RemoveField('Comment', 'comment'),
        migrations.RemoveField('Comment', 'filipino_comment'),
        migrations.RenameField('Comment', 'date', 'timestamp'),
        migrations.RemoveField('Comment', 'average_score'),
        migrations.RemoveField('Comment', 'number_rated'),
        migrations.AlterField('Comment', 'tag',
                              models.CharField(max_length=256, blank=True, default='')),
        migrations.RemoveField('Comment', 'original_language'),
        migrations.RemoveField('Comment', 'se'),

        # Renaming `Rating` to `QuantitativeQuestionRating` is broken
        migrations.CreateModel('QuantitativeQuestionRating', [
            ('respondent', models.ForeignKey('Respondent', on_delete=models.CASCADE)),
            ('timestamp', models.DateTimeField(auto_now_add=True)),
            ('score', models.SmallIntegerField(default=-2)),
            ('question', models.ForeignKey('QuantitativeQuestion', on_delete=models.CASCADE)),
        ], {
            'unique_together': ('respondent', 'question')
        }),
        migrations.RunPython(populate_quantitative_question_ratings),
        migrations.DeleteModel('Rating'),

        migrations.AddField('CommentRating', 'respondent',
                            models.ForeignKey('Respondent', on_delete=models.CASCADE, default=0), preserve_default=False),
        migrations.RunPython(populate_comment_rating_respondent_forward),
        migrations.RemoveField('CommentRating', 'user'),
        migrations.AddField('CommentRating', 'comment',
                            models.ForeignKey('Comment', on_delete=models.CASCADE, default=0), preserve_default=False),
        migrations.RunPython(populate_comment_rating_comment_forward),
        migrations.RemoveField('CommentRating', 'cid'),
        migrations.AlterField('CommentRating', 'score', models.SmallIntegerField(default=-2)),
        migrations.RenameField('CommentRating', 'date', 'timestamp'),
        migrations.RemoveField('CommentRating', 'accounted'),

        migrations.RunPython(delete_duplicate_comment_ratings_forward),
        migrations.AlterUniqueTogether('CommentRating', ('respondent', 'comment')),

        migrations.RemoveField('Respondent', 'user'),
    ]
