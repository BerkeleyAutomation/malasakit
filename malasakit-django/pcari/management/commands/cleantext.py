"""
cleantext -- Utility for cleaning text fields in batches from the command line
"""

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import CharField, TextField

from pcari import models


class Command(BaseCommand):
    help = 'Cleans character and text fields'

    def add_arguments(self, parser):
        parser.add_argument('fields', nargs='+', help='A sequence of '
                            'model-field name pairs, such as `Model.field`')

    def clean_text_field(self, model_name, field_name, empty_value=None):
        model = getattr(models, model_name)
        field = model._meta.get_field(field_name)
        if not isinstance(field, (CharField, TextField)):
            raise TypeError
        if empty_value is None and not field.null:
            raise ValueError('cannot set `None` on non-nullable field')

        num_cleaned, joined_name = 0, model_name + '.' + field_name
        for instance in model.objects.all():
            raw_value = getattr(instance, field_name)
            if raw_value != empty_value:
                cleaned_value = raw_value.strip() or empty_value
                if cleaned_value != raw_value:
                    setattr(instance, field_name, cleaned_value)
                    message = 'Cleaned `{0}` of instance with PK {1}'
                    self.stdout.write(message.format(joined_name, instance.pk))
                    # instance.save()
                    num_cleaned += 1

        message = ':: Cleaned a total of {0} `{1}` fields'
        self.stdout.write(message.format(num_cleaned, joined_name))

    def handle(self, *args, **options):
        for field in options['fields']:
            try:
                model_name, field_name = field.split('.')
            except ValueError:
                raise CommandError('failed to parse model-field pair `{0}`'
                                   .format(field))

            try:
                self.clean_text_field(model_name, field_name)
            except (FieldDoesNotExist, AttributeError, TypeError) as e:
                print(e)
                raise CommandError('`{0}.{1}` is not a text field'
                                   .format(model_name, field_name))
            except Exception as exc:
                raise CommandError(str(exc))
