from __future__ import unicode_literals
import logging
import sys

from django.apps import AppConfig


class PCARIConfig(AppConfig):
    name = 'pcari'

    def ready(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(levelname)s :: %(message)s')

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.log(logging.INFO, 'Logging initialized')
