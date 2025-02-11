from django.conf import settings
from django.db import models
from django.apps import apps


class AuditBase(models.Model):
    """
    Abstract base class with audit fields
    """
    created = models.DateTimeField(null=True, auto_now_add=True)
    updated = models.DateTimeField(null=True, auto_now=True)

    created_by = models.UUIDField(blank=True, null=True, serialize=True)
    last_updated_by = models.UUIDField(blank=True, null=True, serialize=True)

    class Meta:
        abstract = True

    def  save(self, *args, **kwargs):
        from common_core.middleware.thread_local_middleware import get_current_user
        user = get_current_user()
        if user:
            if self._state.adding:
                self.created_by = user.id
            self.last_updated_by = user.id
        super().save(*args, **kwargs)

    save.alters_data = True

    def get_created_by_user(self):
        UserModel = apps.get_model(settings.AUTH_USER_MODEL)
        if self.created_by != 0:
            return UserModel.objects.get(pk=self.created_by)
        return None

    def get_updated_by_user(self):
        UserModel = apps.get_model(settings.AUTH_USER_MODEL)
        if self.last_updated_by != 0:
            return UserModel.objects.get(pk=self.last_updated_by)
        return None
