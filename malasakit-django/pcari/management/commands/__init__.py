"""
This module defines common command templates.
"""

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model

from pcari import models


class BatchProcessingCommand(BaseCommand):
    """
    A `BatchProcessingCommand` provides utilities for manipulating a sequence
    of fields, which would be useful for cleaning or exporting data.
    """
    def add_arguments(self, parser):
        parser.add_argument('fields', nargs='+', help="A sequence of "
                            "model-field name pairs in the form 'Model.field'")

    def precondition_check(self, options, model, field):
        """
        Inspect the given model and field, and raise exceptions as necessary.
        """
        pass  # By default, make no checks

    def preprocess(self, options):
        """
        Prepare to batch process all fields (e.g. open files).
        """
        pass

    def process(self, options, instance, model_name, field_name):
        """
        Given a model instance and the field to operate on, perform an action.
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
                model = getattr(models, model_name)
                assert issubclass(model, Model), 'not a Django model'
                field = model._meta.get_field(field_name)
                self.precondition_check(options, model, field)
            except Exception as exc:
                message = 'model or field failed precondition check: {0}'
                raise CommandError(message.format(str(exc)))

            for instance in model.objects.all():
                self.process(options, instance, model_name, field_name)

        self.postprocess(options)

    def postprocess(self, options):
        """
        Terminate the processing job (e.g. close files).
        """
        pass
