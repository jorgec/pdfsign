from django.db import models
from django.db.models import Q


class ThreadAwareBaseManager(models.Manager):
    """
    Abstract class with helper functions relating to request object
    """

    def all_by_current_user(self):
        from common_core.middleware.thread_local_middleware import get_current_user
        user = get_current_user()
        if not user:
            return []

        queryset = super().get_queryset()

        try:
            if user.is_admin:
                return queryset
            return queryset.filter(Q(created_by=user.pk) | Q(created_by=None))
        except AttributeError:
            return []
