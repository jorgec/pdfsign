from django import forms
from .models import Signature

class SignatureUploadForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ["image"]
        widgets = {
            "image": forms.FileInput(attrs={"accept": "image/png, image/jpeg"})
        }
