# Generated by Django 3.2.12 on 2022-07-12 12:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_prefixctl", "0009_reftag_asnmon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alertlogrecipient",
            name="alertlog",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alert_log_recipient_set",
                to="django_prefixctl.alertlog",
            ),
        ),
        migrations.AlterModelTable(
            name="alertlogrecipient",
            table="prefixctl_alert_log_recipient",
        ),
    ]
