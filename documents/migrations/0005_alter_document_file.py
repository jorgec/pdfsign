# Generated by Django 4.2.1 on 2025-02-12 14:49

from django.db import migrations, models
import documents.models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_alter_signaturefield_field_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(max_length=512, upload_to=documents.models.document_upload_path),
        ),
    ]
