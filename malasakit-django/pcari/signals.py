""" This module defines actions that should be taken on special events. """

from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

from .models import History


@receiver(pre_delete)
def store_successors(**kwargs):
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

        if instance.predecessor is not None:
            instance.predecessor.active = instance.active
            instance.predecessor.save()
