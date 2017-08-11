"""
This module defines actions that should be taken on special events.

References:
    * `Django Reference on Signals <https://docs.djangoproject.com/en/dev/topics/signals/>`_
"""

from __future__ import unicode_literals

from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

from pcari.models import History


@receiver(pre_delete)
def store_successors(**kwargs):
    """ Stash an instance's successors prior to deletion. """
    sender, instance = kwargs['sender'], kwargs['instance']
    if issubclass(sender, History):
        query = sender.objects.using(kwargs['using'])
        # pylint: disable=protected-access
        instance._successors = list(query.filter(predecessor=instance))


@receiver(post_delete)
def resolve_history_on_deletion(**kwargs):
    """
    Ensure that instances of models that derive from `History` do not have a
    dangling pointer to a predecessor.
    """
    sender, instance = kwargs['sender'], kwargs['instance']
    if issubclass(sender, History):
        for successor in getattr(instance, '_successors', []):
            successor.predecessor = instance.predecessor
            successor.save()

        # FIXME
        try:
            if instance.predecessor is not None:
                instance.predecessor.active = instance.active
                instance.predecessor.save()
        except sender.DoesNotExist:
            pass
