from django.contrib import admin
from documents.models import Document, SignatureField

# Register your models here.
admin.site.register(Document)
admin.site.register(SignatureField)
