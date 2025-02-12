import os
import shutil

from django.core.files.base import File
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
    file = models.FileField(upload_to=document_upload_path, max_length=512)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    signed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.file.name} (Uploaded by {self.owner.username})"

    def get_latest_document(self):
        """
        Checks for the existence of a signed version of the document and returns its path if it exists.

        Returns:
            The path to the signed document if it exists, None otherwise.
        """
        signed_doc_path = os.path.join(
            settings.MEDIA_ROOT,
            "signed_documents",
            "documents",
            self.owner.username,
            os.path.basename(self.file.name),  # Use original filename
        )
        if os.path.exists(signed_doc_path):
            return signed_doc_path  # Return self for chaining

        return None  # Return None if signed version doesn't exist

    def update_signed_document(self, signed_doc_path):
        """
                Copies the file from signed_doc_path to the Document's file field,
                overwriting the existing file.

                Args:
                    signed_doc_path: The path to the signed document.

                Returns:
                    The Document instance (self) for chaining, or None if an error occurs.
                """
        try:
            # 1. Construct the *full* path to the Document's file location.
            destination_path = os.path.join(settings.MEDIA_ROOT, self.file.name)

            # Ensure the directory exists.
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # 2. Copy the signed document to the Document's file location.
            shutil.copy2(signed_doc_path, destination_path)  # copy2 preserves metadata

            return self  # Return self for chaining

        except FileNotFoundError:
            print(f"Error: Signed document not found at {signed_doc_path}")
            return None
        except Exception as e:
            print(f"Error copying file: {e}")
            return None

    def check_complete(self):
        """
        Checks if all assigned signature fields for this document have been signed.

        Returns:
            True if all fields are signed, False otherwise.
        """
        total_fields = self.signature_fields.count()
        signed_fields = self.signature_fields.filter(signed=True).count()
        return signed_fields == total_fields


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
