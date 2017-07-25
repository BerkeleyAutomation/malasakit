"""
Prepare a translation file from text stored in the database
"""

from __future__ import print_function, unicode_literals

from django.db.models import CharField, TextField

from pcari.management.commands import BatchProcessingCommand


class Command(BatchProcessingCommand):
    """
    This command pulls text from the database and prepares them for translation.
    """
    help = 'Exports text fields in the database for translation'
    OUTPUT_FILE_KEY = 'output-file'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('-o', '--output', required=True,
                            help='A path to a file to write to')

    def precondition_check(self, options, model, field):
        super(Command, self).precondition_check(options, model, field)
        message = "'{0}' is not a text field"
        assert isinstance(field, (CharField, TextField)), message

    def preprocess(self, options):
        super(Command, self).preprocess(options)
        output_file = open(options['output'], 'w+')
        options[self.OUTPUT_FILE_KEY] = output_file

        # Write header
        print('msgid ""', file=output_file)
        print('msgstr "Content-Type: text/plain; charset=UTF-8\\n"',
              file=output_file, end='\n'*2)

    def process(self, options, instance, model_name, field_name):
        """
        Write strings to a `.pot` file that can be merged with Django's own
        translations (i.e. `django.pot`) using GNU `msgcat`.
        """
        value = getattr(instance, field_name)
        if value:
            output_file = options[self.OUTPUT_FILE_KEY]

            comment = '#: {0}.{1}:{2}'
            comment = comment.format(model_name, field_name, instance.pk)
            print(comment, file=output_file)

            print('msgid "{0}"'.format(value).encode('utf-8'), file=output_file)
            print('msgstr ""', file=output_file, end='\n'*2)

    def postprocess(self, options):
        super(Command, self).postprocess(options)
        options[self.OUTPUT_FILE_KEY].close()
