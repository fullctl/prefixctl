# Generated by Django 4.2.10 on 2024-02-28 19:05

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("django_prefixctl", "0016_alter_asnset_slug_alter_prefixset_slug"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="prefixmonitor",
            name="asn_set_origin",
        ),
        migrations.RemoveField(
            model_name="prefixmonitor",
            name="asn_set_upstream",
        ),
        migrations.RemoveField(
            model_name="prefixmonitor",
            name="instance",
        ),
        migrations.RemoveField(
            model_name="prefixmonitor",
            name="prefix_set",
        ),
        migrations.RemoveField(
            model_name="prefixmonitor",
            name="task_schedule",
        ),
        migrations.DeleteModel(
            name="PrefixMonitorTask",
        ),
        migrations.DeleteModel(
            name="PrefixMonitor",
        ),
    ]
