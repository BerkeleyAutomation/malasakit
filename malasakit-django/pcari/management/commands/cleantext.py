"""
cleantext -- Utility for batch-cleaning text fields from the command line
"""

from django.db.models import CharField, TextField

from . import BatchProcessingCommand


class Command(BatchProcessingCommand):
    """
    This command performs basic text cleaning on fields specified by the user.
    """
    help = 'Cleans character and text fields'

    def add_arguments(self, parser):
        """
        Enable the user to set a sentinel value empty strings are replaced with.
        """
        super(Command, self).add_arguments(parser)
        parser.add_argument('--empty-value', nargs=1, default=None,
                            help='Text to substitute empty strings with '
                                 '(by default: use a NULL value)')

    def precondition_check(self, options, model, field):
        """
        Verify the field contains text and is compatible with the empty value.
        """
        super(Command, self).precondition_check(options, model, field)

        message = "'{0}' is not a text field".format(field.name)
        assert isinstance(field, (CharField, TextField)), message

        message = "cannot set 'None' on a non-nullable field '{0}'"
        message = message.format(field.name)
        assert options['empty_value'] is not None or field.null, message

    def process(self, options, instance, model_name, field_name):
        """
        Clean leading and trailing whitespace and replace empty strings.
        """
        raw_value = getattr(instance, field_name)
        if raw_value != options['empty_value']:
            cleaned_value = raw_value.strip() or options['empty_value']
            if cleaned_value != raw_value:
                setattr(instance, field_name, cleaned_value)
                instance.save()

                message = "Cleaned '{0}' of instance with PK {1}"
                self.stdout.write(message.format(model_name + '.' + field_name,
                                                 instance.pk))
