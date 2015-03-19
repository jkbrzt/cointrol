"""
Utils for working with heterogeneous models and Django model inheritance.

"""
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.dispatch import receiver


class CastableQuerySet(QuerySet):

    def get(self, *args, **kwargs):
        """Return a casted model."""
        return super(CastableQuerySet, self).get(*args, **kwargs).cast()

    def casted(self):
        """Return a `list` of casted instances."""
        return (model.cast() for model in self)


class CastableManager(models.Manager):
    """A manager using `CastableQuerySet`."""

    def get_queryset(self):
        return CastableQuerySet(self.model, using=self._db)\
            .select_related('leaf_content_type')


class CastableModel(models.Model):
    # This is the reference to the leaf subclass' ``ContentType``
    # instance that allows us to cast the class to it:
    leaf_content_type = models.ForeignKey(
        ContentType,
        verbose_name='leaf type',
        editable=False,
        null=True
    )

    objects = models.Manager()
    casted = CastableManager()

    def cast(self):
        """Return an instance of the leaf class."""
        if not self.leaf_content_type:
            return self
        try:
            leaf_object = self.__casted
        except AttributeError:
            leaf_object = self.__casted = self.leaf_content_type\
                .get_object_for_this_type(pk=self.pk)
        return leaf_object

    class Meta:
        abstract = True


# noinspection PyUnusedLocal
@receiver(models.signals.pre_save, dispatch_uid='castable.models.pre_save')
def castable_instance_pre_save(sender, instance, *args, **kwargs):
    """Set the model instance's ``leaf_content_type``
    attribute if the instance is a ``CastableModel``
    and doesn't have one yet.

    """
    if (isinstance(instance, CastableModel)
            and CastableModel not in type(instance).__bases__
            and not instance.leaf_content_type_id):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        instance.leaf_content_type = content_type
