# Generated by Django 3.2.15 on 2023-02-20 15:44

import netfields.fields
from django.db import migrations, models


def forwards(apps, schema_editor):
    Data = apps.get_model("prefix_meta", "Data")

    for meta_data in Data.objects.all():
        meta_data.date = meta_data.updated
        meta_data.save()


class Migration(migrations.Migration):
    dependencies = [
        ("prefix_meta", "0003_auto_20220405_1039"),
    ]

    operations = [
        migrations.AddField(
            model_name="data",
            name="source_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="data",
            name="date",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="data",
            name="prefix",
            field=netfields.fields.CidrAddressField(max_length=43),
        ),
        migrations.AlterUniqueTogether(
            name="data",
            unique_together={("source_name", "prefix")},
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
