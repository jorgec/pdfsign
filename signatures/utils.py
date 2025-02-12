import os
from django.conf import settings
from .models import Signature


def get_user_signature_path(user):
    """Return the path of the user's signature image for PyHanko"""
    try:
        signature = Signature.objects.get(user=user)
        if signature.image:
            path = os.path.join(settings.MEDIA_ROOT, signature.image.name)
            if os.path.exists(path):
                return path
    except Signature.DoesNotExist:
        return None
    return None
