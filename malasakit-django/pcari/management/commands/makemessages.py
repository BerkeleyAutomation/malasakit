"""
Prepare message files for translators
"""

import os

from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """ Extend the default `makemessages` command. """
    def write_po_file(self, potfile, locale):
        """
        Before merging the `.pot` file with an existing `.po` file, merge other
        `.pot` files together (use in conjunction with `makedbtrans`).
        """
        # Using `os.system` isn't great, but it will do for now
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
