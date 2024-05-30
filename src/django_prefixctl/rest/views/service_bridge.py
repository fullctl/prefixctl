from django.db.models import Q

from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import (
    DataViewSet,
    HeartbeatViewSet,
    StatusViewSet,
    MethodFilter,
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
        ("org", "instance__org__slug"),
        ("q", MethodFilter("autocomplete")),
        ("slug", "slug"),
        ("ids", "id__in")
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = models.PrefixSet.objects.filter(status="ok")
    serializer_class = Serializers.prefix_set

    def filter_autocomplete(self, qset, value:str):
        return models.PrefixSet.objects.filter(
            Q(name__icontains=value) | Q(slug__icontains=value)
        )