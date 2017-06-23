""" This module defines actions that should be taken on special events. """

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import History


@receiver(pre_delete)
def resolve_history_on_deletion(**kwargs):
    """
    Ensure that child instances of models that derive from `History` do not
    have a dangling pointer.
    """
    sender, instance, using = kwargs['sender'], kwargs['instance'], kwargs['using']
    if issubclass(sender, History):
        for successor in sender.objects.using(using).filter(predecessor=instance):
            successor.predecessor = instance.predecessor
            successor.save()

        if instance.predecessor is not None:
            instance.predecessor.active = instance.active
            instance.predecessor.save()
