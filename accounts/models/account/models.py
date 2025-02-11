"""
Account model

---
Jorge Cosgayon
"""
import logging

from django.apps import apps
from django.contrib.auth.models import (
    AbstractBaseUser, Group, Permission
)
from django.core.validators import RegexValidator
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver

from common_core.models import IdentityBase, AuditBase, SoftDeleteBase
from common_core.models.meta import MetaBase
from .constants import USERNAME_REGEX
from .managers import AccountManager

logger = logging.getLogger(__name__)


class Account(IdentityBase, AuditBase, MetaBase, AbstractBaseUser):
    """
    Base Account model
    Fields:
        - username: CharField
        - email: EmailField
        - is_active: BooleanField
        - is_admin: BooleanField
        - user_settings: JSONField
    """
    # Fields
    username = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=USERNAME_REGEX,
                message='Username can only contain alphanumeric characters and the following characters: . -',
                code='Invalid Username'
            )
        ],
        unique=True,
        null=False

    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, module_slug):
        if self.is_admin:
            return True
        return False

    def has_perms(self, perms: str):
        if self.is_admin:
            return True
        return len(self.shkolamodulemembership_set.filter(module_role__permissions__codename=perms)) > 0

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def is_superuser(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    class Meta:
        ordering = ('username', '-created',)

    ################################################################################
    # Model methods
    # def is_member_of(self, group):
    #     return len(self.groupmembership_set.filter(group=group)) > 0
    #
    # def get_user_groups(self, serialize=False):
    #     groups = self.groupmembership_set.all()
    #     if serialize:
    #         from accounts.models.shkola_modules.serializers import GroupMembershipSerializer
    #         return GroupMembershipSerializer(groups, many=True).data
    #     return groups
    #
    # def get_groups(self, serialize=False):
    #     UserGroup = apps.get_model('accounts.UserGroup')
    #
    #     groups = UserGroup.objects.filter(id__in=[ug.group.id for ug in self.get_user_groups()])
    #     if serialize:
    #         return GroupSerializer(groups, many=True).data
    #     return groups
    #
    # def login_serializer(self):
    #     pass


@receiver(post_save, sender=Account)
def scaffold_account(sender, instance=None, created=False, **kwargs):
    pass
