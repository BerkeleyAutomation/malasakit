"""
This module defines the application configuration.

References:
    * `Defining a Custom Configuration
      <https://docs.djangoproject.com/en/dev/ref/applications/#configuring-applications>`_
"""

from __future__ import unicode_literals

from django.apps import AppConfig


class PCARIConfig(AppConfig):
    """
    Handle application-wide configuration.
    """
    name = 'pcari'
    verbose_name = 'PCARI'

    def ready(self):
        """
        Enable behavior defined in :mod:`pcari.signals` when the application
        starts.
        """
        # pylint: disable=unused-variable
        from pcari import signals
