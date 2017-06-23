"""
This module defines a custom tag for generating URLs for switching languages.
"""

from django import template
from django.conf import settings

# pylint: disable=invalid-name
register = template.Library()


@register.filter
def localize_url(value, language):
    url_root = settings.URL_ROOT
