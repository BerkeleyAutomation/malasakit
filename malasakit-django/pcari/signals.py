"""
This module defines actions that should be taken on special events.

References:
    * `Django Reference on Signals <https://docs.djangoproject.com/en/dev/topics/signals/>`_
"""

from __future__ import unicode_literals

from math import sqrt

from django.db.models.signals import pre_delete, post_delete
from django.db.backends.signals import connection_created
from django.dispatch import receiver

from pcari.models import History


def make_stddev_aggregate(sample=False):
    """
    Create a standard deviation aggregator to pass to PySQLite. In production,
    where performance is critical, the chosen backend (that is, not SQLite)
    should implement standard deviation natively.

    Args:
        sample: Whether the aggregator should calculate the sample standard deviation.

    Returns:
        A class that defines the aggregator.
    """
    class StdDev(object):
        """
        Define an aggregator for calculating standard deviation. In general, an
        aggregator can maintain state, accepts a sequence of values (passed
        into ``step``), and outputs a result at ``finanlize``. Here,
        ``finalize`` returns the standard deviation if there are enough values,
        or ``None`` otherwise.
        """
        def __init__(self):
            self.value_squared_sum, self.value_sum, self.num_values = 0, 0, 0

        def step(self, value):
            if value is not None:
                self.value_squared_sum += value*value
                self.value_sum += value
                self.num_values += 1

        def finalize(self):
            dof = self.num_values - (1 if sample else 0)  # Degrees of freedom
            if dof > 0:
                return (float(self.value_squared_sum) -
                        pow(self.value_sum, 2)/self.num_values)/dof
    return StdDev


@receiver(connection_created)
def extend_sqlite(connection=None, **_):
    """ Monkey-patch custom functions and aggregates if the backend uses SQLite. """
    if connection.vendor == 'sqlite':
        connection.connection.create_function('SQRT', 1, sqrt)
        connection.connection.create_aggregate('STDDEV_POP', 1,
                                               make_stddev_aggregate())
        connection.connection.create_aggregate('STDDEV_SAMP', 1,
                                               make_stddev_aggregate(sample=True))


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

        try:
            if instance.predecessor is not None:
                instance.predecessor.active = instance.active
                instance.predecessor.save()
        except sender.DoesNotExist:
            pass
