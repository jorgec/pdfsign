from django.views.generic.edit import FormView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from .models import Signature
from .forms import SignatureUploadForm
import os


class SignatureUploadView(LoginRequiredMixin, FormView):
    template_name = "signature_upload.html"
    form_class = SignatureUploadForm

    def form_valid(self, form):
        user = self.request.user
        image = form.cleaned_data["image"]

        # Check if user already has a signature and delete the old one
        if hasattr(user, "signature"):
            old_signature = user.signature
            if old_signature.image:
                old_path = old_signature.image.path
                if os.path.exists(old_path):
                    default_storage.delete(old_path)  # Delete old file
            old_signature.image = image  # Replace with new file
            old_signature.save()
        else:
            Signature.objects.create(user=user, image=image)

        return redirect("upload_signature")
