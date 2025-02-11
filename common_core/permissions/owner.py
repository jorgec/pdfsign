from rest_framework import permissions
from django.apps import apps

from accounts.models.account.constants import UserTypeConstants


class IsOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.get_created_by_user() == request.user or request.user.user_type == UserTypeConstants.SUPERADMIN


