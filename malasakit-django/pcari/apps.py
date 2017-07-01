""" This module defines the application configuration. """

from __future__ import unicode_literals

from django.apps import AppConfig


class PCARIConfig(AppConfig):
    """
    This class handles application-wide configuration by preparing resources.
    """
    name = 'pcari'
    verbose_name = 'PCARI'

    def ready(self):
        # pylint: disable=unused-variable
        from . import signals
