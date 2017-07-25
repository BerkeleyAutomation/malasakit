"""
This module defines a custom tag for generating URLs for switching languages.
"""

import posixpath

from django import template
from django.conf import settings

# pylint: disable=invalid-name
register = template.Library()


@register.filter
def localize_url(url_example, language):
    """
    Localize a URL for a given language.

    Args:
        url_example: A sample URL of any language that starts with
            ``settings.URL_ROOT``.
        language: The code of the language to localize for.

    Returns:
        The localized URL as a string.

    >>> # With `settings.URL_ROOT` set to `/pcari`
    >>> localize_url('/pcari/en/landing/', 'tl')
    '/pcari/tl/landing/'
    >>> # With `settings.URL_ROOT` set to '/'
    >>> localize_url('/en/landing', 'tl')
    `/tl/landing`
    """
    if url_example.startswith(settings.URL_ROOT):
        url_root = posixpath.commonprefix([settings.URL_ROOT, url_example])
        assert url_root == settings.URL_ROOT

        relative_url = posixpath.relpath(url_example, url_root)
        components = relative_url.split('/')
        assert len(components) >= 1
        components[0] = language
        localized_url = posixpath.join(url_root, *components)
        if not localized_url.endswith('/'):
            localized_url += '/'
        return localized_url
    return url_example
