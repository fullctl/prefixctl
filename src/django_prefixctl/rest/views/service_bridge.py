from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import (
    DataViewSet,
    HeartbeatViewSet,
    StatusViewSet,
)

import django_prefixctl.models.prefixctl as models
from django_prefixctl.rest.serializers.service_bridge import Serializers


@route
class Status(StatusViewSet):
    checks = ("bridge_aaactl", "bridge_pdbctl")


@route
class Heartbeat(HeartbeatViewSet):
    pass


@route
class PrefixSet(DataViewSet):
    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("org", "org_id"),
        ("q", "name__icontains"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = models.PrefixSet.objects.filter(status="ok")
    serializer_class = Serializers.prefix_set
