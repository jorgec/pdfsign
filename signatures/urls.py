from django.urls import path
from .views import SignatureUploadView

urlpatterns = [
    path("upload/", SignatureUploadView.as_view(), name="upload_signature"),
]