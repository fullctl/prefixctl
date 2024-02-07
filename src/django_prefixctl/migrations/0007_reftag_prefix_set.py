# Generated by Django 3.2.12 on 2022-07-11 13:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_fullctl", "0019_default_org"),
        ("django_prefixctl", "0006_reftag_asn_set"),
    ]

    operations = [
        migrations.RenameField(
            model_name="prefix",
            old_name="pfxset",
            new_name="prefix_set",
        ),
        migrations.RenameField(
            model_name="prefixmonitor",
            old_name="pfxset",
            new_name="prefix_set",
        ),
        migrations.AlterField(
            model_name="prefixset",
            name="instance",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prefix_set_set",
                to="django_fullctl.instance",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="prefix",
            unique_together={("prefix_set", "prefix")},
        ),
        migrations.AlterModelTable(
            name="prefixset",
            table="prefixctl_prefix_set",
        ),
    ]
