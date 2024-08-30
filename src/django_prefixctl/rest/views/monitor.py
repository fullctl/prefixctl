from django.core.exceptions import FieldError
from rest_framework import status, viewsets
from rest_framework.response import Response

from django_prefixctl.rest.api_schema import MonitorSchema
from django_prefixctl.rest.decorators import grainy_endpoint
from django_prefixctl.rest.route.prefixctl import route
from django_prefixctl.rest.serializers.monitor import (
    MONITOR_CLASSES,
    Serializers,
    get_monitor_class,
)


def remove_monitor(request, instance, data: dict) -> Response:
    """
    Remove a monitor from an instance

    Arguments:

    request - the request object
    data - the request data

    Returns:

    A response object
    """

    serializer = Serializers.delete_monitor(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    pk = serializer.validated_data["id"]
    typ = serializer.validated_data["monitor_type"]

    monitor_serializer = get_monitor_class(typ)
    model_class = monitor_serializer.Meta.model
    monitor = model_class.objects.get(pk=pk, instance=instance)

    serializer.context["monitor_instance"] = monitor

    if not request.perms.check(monitor, "delete"):
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer.delete(serializer.validated_data)

    return Response({"type": monitor.HandleRef.tag, "id": pk})


def add_monitor(request, instance, data: dict) -> Response:
    """
    Add a new monitor to an instance

    Arguments:

    request - the request object
    instance - the instance to add the monitor to
    data - the request data

    Returns:

    A response object
    """

    try:
        serializer_cls = get_monitor_class(data["monitor_type"])
        serializer = serializer_cls(data=data, context={"instance": instance})
    except KeyError:
        if "monitor_type" in data:
            return Response(
                {"monitor_type": "Unknown monitor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"monitor_type": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not request.perms.check(serializer.grainy_namespace, "create"):
        return Response(status=status.HTTP_403_FORBIDDEN)

    # Create the monitor instance using serializer.create()
    monitor = serializer.create(serializer.validated_data)

    return Response(
        serializer_cls(instance=monitor).data, status=status.HTTP_201_CREATED
    )


def list_monitors(instance, types: list[str] = None, **filters) -> list[dict]:
    """
    Returns a list of all monitors for a given instance

    Additional filters can be passed to filter the queryset

    Arguments:

    instance - the organization instance to list monitors for
    types - a list of monitor types to filter on (monitor handle ref tag)

    Keyword Arguments:

    Any additional keyword arguments will be passed to the queryset filter. Since
    each monitor type has a different model, the filters will be applied to the
    queryset for that specific monitor type. If the filter is not valid for the
    monitor type, the monitor type will be skipped.
    """

    monitors = []

    for typ, serializer_class in MONITOR_CLASSES.items():
        if types and typ not in types:
            continue

        qset = serializer_class.Meta.model.objects.filter(instance=instance)

        if filters:
            try:
                qset = qset.filter(**filters)
            except FieldError:
                # invalid monitor type for filter
                continue

        serializer = serializer_class(qset, many=True)
        monitors.extend(serializer.data)

    return monitors


@route
class Monitor(viewsets.GenericViewSet):
    schema = MonitorSchema()
    ref_tag = "monitor"

    def get_serializer_dynamic(self, path, method, direction):
        if method == "DELETE":
            return Serializers.delete_monitor()
        return self.get_serializer()

    def get_queryset(self):
        try:
            return MONITOR_CLASSES[
                self.request.data["monitor_type"]
            ].Meta.model.objects.all()
        except KeyError:
            return None

    # using a generic service namespace for access to this endpoint
    # individual monitors will be filted on their individual grainy
    # namespaces
    @grainy_endpoint(namespace="service.prefixctl.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        """
        Lists all monitors for a given organization instance
        """
        return Response(list_monitors(instance))

    # using a generic service namespace for access to this endpoint
    # permission for creation will be checked against the `type` of the submitted
    # monitor
    @grainy_endpoint(namespace="service.prefixctl.{request.org.permission_id}")
    def create(self, request, org, instance, *args, **kwargs):
        """
        Create a new monitor for a given organization instance
        """

        return add_monitor(request, instance, request.data)

    # using a generic service namespace for access to this endpoint
    # permission for update will be checked against the object being updated
    @grainy_endpoint(namespace="service.prefixctl.{request.org.permission_id}")
    def update(self, request, org, instance, pk, *args, **kwargs):
        """
        Update a monitor for a given organization instance
        """

        try:
            serializer_cls = get_monitor_class(request.data["monitor_type"])
        except KeyError:
            return Response(
                {"monitor_type": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model_class = serializer_cls.Meta.model
        monitor = model_class.objects.get(pk=pk, instance=instance)
        serializer = serializer_cls(instance=monitor, data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.perms.check(monitor, "update"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer.update(monitor, serializer.validated_data)

        return Response(serializer_cls(instance=monitor).data)

    # using a generic service namespace for access to this endpoint
    # permission for deletion will be checked against the object being updated
    @grainy_endpoint(namespace="service.prefixctl.{request.org.permission_id}")
    def destroy(self, request, org, instance, pk, *args, **kwargs):
        """
        Remove a monitor for a given organization instance
        """
        
        return remove_monitor(request, instance, request.data)
