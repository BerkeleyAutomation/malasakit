from django import template

register = template.Library()


@register.filter
def localize_url(value, language):
    pass
