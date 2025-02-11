from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone


class SoftDeleteBaseQuerySet(QuerySet):
    """
    Prevents objects from being hard-deleted. Instead, sets the
    ``date_deleted``, effectively soft-deleting the object.
    """
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)


class SoftDeleteBaseManager(models.Manager):
    """
    Only exposes objects that have NOT been soft-deleted.
    """

    def get_queryset(self):
        return SoftDeleteBaseQuerySet(self.model, using=self._db).filter(
            deleted_on__isnull=True
        )

    def all(self):
        return self.get_queryset()

    def filter(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs)


class SoftDeleteBase(models.Model):
    """
    Abstract base class with soft deletes
    """
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.UUIDField(null=True, blank=True, serialize=True)

    objects = SoftDeleteBaseManager()

    # original_objects = models.Manager()

    class Meta:
        abstract = True

    def undelete(self):
        self.deleted_on = None
        self.deleted_by = 0
        self.save()

    def delete(self, using=None, keep_parents=False, force=False):
        if force:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            from common_core.middleware.thread_local_middleware import get_current_user
            user = get_current_user()
            self.deleted_on = timezone.now()
            if user:
                self.deleted_by = user.pk
            super().save()

    delete.alters_data = True

    def get_deleted_by_user(self):
        if self.deleted_by != 0:
            return settings.AUTH_USER_MODEL.objects.get(pk=self.deleted_by)
        return None
