"""
Utility for batch-cleaning text fields from the command line
"""

from django.db.models import CharField, TextField

from pcari.management.commands import BatchProcessingCommand


class Command(BatchProcessingCommand):
    """
    This command performs basic text cleaning on fields specified by the user.
    """
    help = 'Cleans character and text fields'

    def precondition_check(self, options, model, field):
        """
        Verify the field contains text and is compatible with the empty value.
        """
        super(Command, self).precondition_check(options, model, field)

        message = "'{0}' is not a text field".format(field.name)
        assert isinstance(field, (CharField, TextField)), message

    def process(self, options, instance, model_name, field_name):
        """
        Clean leading and trailing whitespace and replace empty strings.
        """
        raw_value = getattr(instance, field_name)
        cleaned_value = raw_value.strip()
        if cleaned_value != raw_value:
            setattr(instance, field_name, cleaned_value)
            instance.save()

            message = "Cleaned '{0}' of instance with PK {1}"
            self.stdout.write(message.format(model_name + '.' + field_name,
                                             instance.pk))
