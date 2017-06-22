from __future__ import unicode_literals

import logging
import os
import sys

import yaml
from django.apps import AppConfig
from django.conf import settings



class PCARIConfig(AppConfig):
    name = 'pcari'
    verbose_name = 'PCARI'

    def initialize_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(levelname)s :: %(message)s')

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.log(logging.INFO, 'Logging initialized')

    def read_province_names(self):
        logger = logging.getLogger(self.name)
        path = os.path.join(settings.BASE_DIR, PCARIConfig.name,
                            'config', 'province-names.yaml')

        if os.path.exists(path):
            with open(path) as names_file:
                self.province_names = yaml.load(names_file)
                logger.log(logging.INFO, 'Successfully loaded province names')
        else:
            self.province_names = []
            logger.log(logging.WARNING,
                       'Could not find province names file at: ' + path)

    def ready(self):
        import signals
        self.initialize_logger()
        self.read_province_names()
