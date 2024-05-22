# Generated by Django 3.2.17 on 2023-03-08 11:38

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "prefix_meta",
            "0014_bgpupdates_bgpupdatesdata_historicalwhois_historicalwhoisdata_rdapdata_rdaprequest_ripestatdata_ripe",
        ),
    ]

    operations = [
        migrations.AddIndex(
            model_name="data",
            index=models.Index(django.db.models.expressions.F("date"), name="date_idx"),
        ),
        migrations.AddIndex(
            model_name="data",
            index=models.Index(django.db.models.expressions.F("type"), name="type_idx"),
        ),
        migrations.AddIndex(
            model_name="data",
            index=models.Index(fields=["prefix", "type"], name="prefix_type_idx"),
        ),
    ]