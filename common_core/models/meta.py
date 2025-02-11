from django.db import models


class MetaBase(models.Model):
    meta = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        abstract = True
