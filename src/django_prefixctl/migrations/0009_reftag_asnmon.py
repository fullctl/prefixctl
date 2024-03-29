# Generated by Django 3.2.12 on 2022-07-12 12:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_fullctl", "0019_default_org"),
        ("django_prefixctl", "0008_reftag_prefix"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asnmonitor",
            name="asn_set",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="asn_monitor_set",
                to="django_prefixctl.asnset",
            ),
        ),
        migrations.AlterField(
            model_name="asnmonitor",
            name="instance",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="asn_monitor_set",
                to="django_fullctl.instance",
            ),
        ),
        migrations.AlterModelTable(
            name="asnmonitor",
            table="prefixctl_asn_monitor",
        ),
    ]
