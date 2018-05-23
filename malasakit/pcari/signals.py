"""
This module defines actions that should be taken on special events.

References:
    * `Django Reference on Signals <https://docs.djangoproject.com/en/dev/topics/signals/>`_
"""

from __future__ import unicode_literals
from math import sqrt

from django.db.backends.signals import connection_created
from django.dispatch import receiver


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
                stddev2 = (self.value_squared_sum -
                           float(pow(self.value_sum, 2))/self.num_values)/dof
                return sqrt(stddev2)
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
