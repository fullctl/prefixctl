from django.urls import include, path

# import django_prefixctl.rest.views
from django_prefixctl import views

urlpatterns = [
    path(
        "api/",
        include(
            ("django_prefixctl.rest.urls.prefixctl", "prefixctl_api"),
            namespace="prefixctl_api",
        ),
    ),
    path("<str:org_tag>/", views.view_instance, name="prefixctl-home"),
    path("", views.org_redirect),
]
