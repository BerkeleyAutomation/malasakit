"""
This module defines common command templates.

References:
  * `Writing Custom Commands
    <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/>`_
  * `Python Argument Parser Reference
    <https://docs.python.org/2/library/argparse.html#the-add-argument-method>`_
"""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError


class BatchProcessingCommand(BaseCommand):
    """
    A ``BatchProcessingCommand`` provides utilities for manipulating a sequence
    of fields, which would be useful for cleaning or exporting data.
    """
    def add_arguments(self, parser):
        parser.add_argument('fields', nargs='+', help="A sequence of "
                            "model-field name pairs in the form 'Model.field'")

    def precondition_check(self, options, model, field):
        """
        Raise exceptions as necessary prior to processing model instances.

        Args:
            options (dict): Keyword arguments from the command line.
            model: The model to be inspected.
            field: The field of ``model`` to be inspected.

        Raises:
            CommandError: if some precondition is not met.
        """
        pass  # By default, make no checks

    def preprocess(self, options):
        """
        Prepare to batch process all fields (e.g. open files).

        Args:
            options (dict): Keyword arguments from the command line.
        """
        pass

    def process(self, options, instance, model_name, field_name):
        """
        Given a model instance and the field to operate on, perform an action.

        Args:
            options (dict): Keyword arguments from the command line.
            instance: The model instance to be processed.
            model_name (str): The name of the model of ``instance``.
            field_name (str): The name of the field to be processed.
        """
        raise NotImplementedError

    def handle(self, *args, **options):
        self.preprocess(options)

        for model_field_pair in options['fields']:
            components = model_field_pair.split('.')
            if len(components) != 2:
                message = "failed to parse model-field pair '{0}'"
                raise CommandError(message.format(model_field_pair))
            model_name, field_name = components

            try:
                models = ContentType.objects.filter(app_label='pcari')
                model = models.get(model=model_name.lower()).model_class()
                field = model._meta.get_field(field_name)
                self.precondition_check(options, model, field)
            except Exception as exc:
                message = 'model or field failed precondition check: {0}'
                raise CommandError(message.format(unicode(exc)))

            for instance in model.objects.all():
                self.process(options, instance, model_name, field_name)

        self.postprocess(options)

    def postprocess(self, options):
        """
        Terminate the processing job (e.g. close files).

        Args:
            options (dict): Keyword arguments from the command line.
        """
        pass
