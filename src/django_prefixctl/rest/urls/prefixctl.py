from django.urls import include, path

import django_prefixctl.rest.route.prefixctl
import django_prefixctl.rest.views.monitor
import django_prefixctl.rest.views.prefixctl

urlpatterns = [
    path("", include(django_prefixctl.rest.route.prefixctl.router.urls)),
]
