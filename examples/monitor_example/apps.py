from django.apps import AppConfig


class MonitorExampleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitor_example"

    def ready(self):
        # make sure serializers are imported.
        pass
