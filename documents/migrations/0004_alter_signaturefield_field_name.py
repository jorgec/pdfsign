# Generated by Django 4.2.1 on 2025-02-12 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_signaturefield_height_signaturefield_width'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signaturefield',
            name='field_name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
