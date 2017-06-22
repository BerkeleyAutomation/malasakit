import os

from django.core.management.commands import makemessages


class Command(makemessages.Command):
    def write_po_file(self, potfile, locale):
        dirname = os.path.dirname(potfile)
        for filename in os.listdir(dirname):
            if filename.endswith('.pot'):
                cmd = 'msguniq {0} {1} -o {1}'.format(
                    ' '.join(self.msguniq_options),
                    os.path.join(dirname, filename),
                )
                os.system(cmd)

        cmd = 'msgcat {0} > {1}'.format(
            os.path.join(dirname, '*.pot'),
            os.path.join(dirname, 'tmp.pot')
        )
        os.system(cmd)

        os.rename(os.path.join(dirname, 'tmp.pot'),
                  os.path.join(dirname, '{0}.pot'.format(self.domain)))

        super(Command, self).write_po_file(potfile, locale)