import random
import string

from django.apps import apps
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import QuerySet

from common_core.models.soft_deletes import SoftDeleteBaseManager


class AccountQuerySet(QuerySet):
    def actives(self):
        return self.filter(is_active=True)


class AccountManager(BaseUserManager):
    def actives(self):
        return AccountQuerySet(self.model, using=self._db).actives()

    def create_user(self, password, username, email=None):
        """
        Create base user
        :param email:
        :param username:
        :param password:

        :return: Account or False
        """
        if email:
            email_validator = EmailValidator()
            try:
                email_validator(email)
                email = self.normalize_email(email)
            except ValidationError as e:
                raise ValidationError(e)

        reset_key = ''.join(random.choice(string.ascii_lowercase) for i in range(64))

        user = self.model(
            username=username,
            email=email,
            meta={
                "triggers": {
                    "fresh": True
                },
                "reset_key": reset_key
            }
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, username, password, email=None):
        user = self.create_user(
            username=username,
            password=password,
            email=email,
        )
        user.is_admin = True

        user.save(using=self._db)

        return user
