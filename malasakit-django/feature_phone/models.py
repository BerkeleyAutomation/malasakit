from __future__ import unicode_literals

from django.conf import settings
from django.db import models


# Create your models here.

class History(models.Model):
    """
    The ``History`` abstract model records how one model instance derives from
    another.

    The database should be insert-only such that when updating a field of a
    model instance, a new instance is created, rather than overwriting the
    attribute of an old instance. This model effectively implements a primitive
    form of version control to determine which instances are active and how
    instances have been edited.

    Attributes:
        predecessor: A reference to the instance this instance is based on. If
            this instance is the first of its kind (e.g., a new question), this
            reference should be `None` (which is the default value). This
            allows for a tree structure of revisions, where the ``predecessor``
            points to a "parent node" (analogous to ``git`` without merging).
            A sequence of predecessors should never be cyclical.
        active (bool): A flag indicating whether this instance is considered
            usable or not. Typically, when a new model instance is created from
            an old one when updating a field, the old instance is marked as
            inactive.
        predecessors: A generator of predecessors, from the most recent to the
            original. Analogous to crawling up the revision tree.
    """
    predecessor = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, blank=True, default=None,
                                    related_name='successors')
    active = models.BooleanField(default=True)

    def make_copy(self):
        """
        Make a copy of the current model, excluding unique fields.

        Returns:
            An unsaved copy of ``self``.
        """
        model = self.__class__
        copy = model()
        for field in get_direct_fields(model):
            if field.editable and not field.unique:
                value = getattr(self, field.name)
                setattr(copy, field.name, value)

        return copy

    def diff(self, other):
        """
        Find fields where the two instances have different values.

        Args:
            other: An instance of the same model.

        Yields:
            str: A field name where the two instances have different values.

        Raises:
            AssertionError: if ``self`` and ``other`` are not instances of the
                same model.
        """
        model = self.__class__
        assert isinstance(other, model)
        for field in get_direct_fields(model):
            if getattr(self, field.name) != getattr(other, field.name):
                yield field.name

    @property
    def predecessors(self):
        current = self
        while current.predecessor is not None:
            current = current.predecessor
            yield current

    class Meta:
        abstract = True



class Response(History):
    """
    A ``Response`` is an abstract model of respondent-generated data.

    Attributes:
        respondent: A reference to the response author.
        timestamp (datetime.datetime): When this response was made. (By
            default, this field is automatically set to the time when the
            instance is created. This field is not editable.)
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Rating(Response):
    """
    A ``Rating`` is an abstract model of a numeric response.

    Attributes:
        audio: A FilePathField pointing to the audio recording of the rating.
    """

    audio = models.FilePathField(path=MEDIA_ROOT)
    # audio files in the media directory

    class Meta:
        abstract = True
