""" This module defines the application configuration. """

from __future__ import unicode_literals

import json
import logging
import os

from django.apps import AppConfig
from django.conf import settings
import yaml


class PCARIConfig(AppConfig):
    """
    This class handles application-wide configuration by preparing resources.
    """
    name = 'pcari'
    verbose_name = 'PCARI'

    RESOURCE_FILENAMES = ['data/location-data.json']

    def __init__(self, *args, **kwargs):
        super(PCARIConfig, self).__init__(*args, **kwargs)
        self.resources = {}

    def initialize_logger(self):
        """ Configure a logger for printing to standard output. """
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        # formatter = logging.Formatter('[%(asctime)s] %(levelname)s :: %(message)s')

        # console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setLevel(logging.DEBUG)
        # console_handler.setFormatter(formatter)
        # logger.addHandler(console_handler)

        logger.log(logging.INFO, 'Logging initialized')

    def load_resources(self):
        """ Load resources into memory. """
        for filename in self.RESOURCE_FILENAMES:
            filename = os.path.join(settings.BASE_DIR, 'pcari', filename)
            root, extension = os.path.splitext(filename)
            name = os.path.basename(root)

            try:
                with open(filename) as resource_file:
                    if extension == '.json':
                        self.resources[name] = json.load(resource_file)
                    elif extension == '.yaml':
                        self.resources[name] = yaml.load(resource_file)
                    else:
                        raise ValueError('unsupported extension')
            except IOError:
                self.resources[name] = {}

    def ready(self):
        # pylint: disable=unused-variable
        from . import signals
        self.initialize_logger()
        self.load_resources()
