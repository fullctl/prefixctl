from django.apps import AppConfig


class DjangoPrefixctlConfig(AppConfig):
    name = "django_prefixctl"
    label = "django_prefixctl"

    def ready(self):
        import django_prefixctl.signals  # noqa
