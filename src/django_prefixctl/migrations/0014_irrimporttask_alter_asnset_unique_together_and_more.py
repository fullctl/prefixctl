# Generated by Django 4.2.10 on 2024-02-13 16:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_fullctl", "0032_auto_20230719_1049"),
        ("django_prefixctl", "0013_auto_20240111_1701"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="asnset",
            unique_together={("instance", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="prefixset",
            unique_together={("instance", "name")},
        ),
        migrations.AddField(
            model_name="asnset",
            name="slug",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="prefixset",
            name="slug",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="asnset",
            unique_together={("instance", "slug"), ("instance", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="prefixset",
            unique_together={("instance", "slug"), ("instance", "name")},
        ),
    ]