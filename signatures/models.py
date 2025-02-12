from django.db import models
from django.conf import settings
import os


def signature_upload_path(instance, filename):
    """Generate a file path for storing user signatures."""
    return f"signatures/{instance.user.username}_signature.png"


class Signature(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signature"
    )
    image = models.ImageField(upload_to=signature_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def signature_path(self):
        """Return the full path of the signature for PyHanko"""
        if self.image:
            return os.path.join(settings.MEDIA_ROOT, self.image.name)
        return None

    def __str__(self):
        return f"Signature for {self.user.username}"
