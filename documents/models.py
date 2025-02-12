from django.db import models
from django.conf import settings

def document_upload_path(instance, filename):
    """Generate a file path for storing user documents."""
    return f"documents/{instance.owner.username}/{filename}"

class Document(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents"
    )
    file = models.FileField(upload_to=document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    signed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.file.name} (Uploaded by {self.owner.username})"

class SignatureField(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="signature_fields")
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_signatures"
    )
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    page = models.IntegerField()
    field_name = models.CharField(max_length=255, unique=True)
    signed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assigned_user.username} - {self.field_name} ({self.page})"
