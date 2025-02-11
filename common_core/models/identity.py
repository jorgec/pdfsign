import uuid as uuid

from django.db import models


class IdentityBase(models.Model):
    """
    Abstract base class with a UUID
    """
    id = models.UUIDField(unique=True, default=uuid.uuid4, null=False, editable=False, primary_key=True, serialize=True)

    class Meta:
        abstract = True
