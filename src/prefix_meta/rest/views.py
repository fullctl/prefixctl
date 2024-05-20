import ipaddress

from django_prefixctl.rest.decorators import grainy_endpoint
from django_prefixctl.rest.route.prefixctl import route
from fullctl.django.rest.core import BadRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import prefix_meta.models as models
from prefix_meta.rest.serializers import Serializers
from prefix_meta.tasks import LocationUpdateTask


@route
class PrefixMeta(viewsets.GenericViewSet):

    """
    This is the main viewset for the prefix_meta app. It provides the following
    endpoints:

    - GET /prefix_meta/prefix/{typ}/{ip}/{mask}/: Returns all meta data for a
        given prefix. The type of meta data is specified by the `typ` parameter.
        The `ip` and `mask` parameters specify the prefix in CIDR notation.
    """

    serializer_class = Serializers.prefix_location
    queryset = models.Data.objects.all()

    ref_tag = "meta"

    @action(
        detail=False, url_path="prefix/(?P<typ>[^/]+)/(?P<ip>[^/]+)/(?P<mask>[^/]+)"
    )
    @grainy_endpoint(namespace="meta.prefix.location.{request.org.permission_id}")
    def all_by_type(self, request, org, instance, typ, ip, mask, *args, **kwargs):
        """
        Lists all meta data for a given prefix. The type of meta data is
        specified by the `typ` parameter. The `ip` and `mask` parameters specify
        the prefix in CIDR notation.
        """

        try:
            prefix = ipaddress.ip_network(f"{ip}/{mask}")
        except Exception:
            return BadRequest({"non_field_errors": ["malformed prefix"]})

        try:
            serializer_cls = getattr(Serializers, f"prefix_{typ}")
        except AttributeError:
            return BadRequest({"non_field_errors": [f"invalid meta data type: {typ}"]})

        if typ == "location":
            # TODO: modular
            if not LocationUpdateTask.last_run(f"{prefix}", age=60):
                LocationUpdateTask.create_task(f"{prefix}", user=request.user, org=org)

        qset = models.Data.objects.filter(
            prefix__net_contains_or_equals=prefix,
            type=typ,
        ).order_by("prefix")

        serializer_cls = getattr(Serializers, f"prefix_{typ}")

        serializer = serializer_cls(
            qset,
            many=True,
        )
        return Response(serializer.data)
