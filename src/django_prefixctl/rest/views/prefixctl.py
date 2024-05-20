from datetime import timedelta

from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.decorators import load_object
from fullctl.django.rest.mixins import CachedObjectMixin, SlugObjectMixin
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

import django_prefixctl.models as models
from django_prefixctl.rest.api_schema import ASNSetSchema, PrefixSetSchema
from django_prefixctl.rest.decorators import grainy_endpoint
from django_prefixctl.rest.route.prefixctl import route
from django_prefixctl.rest.serializers.monitor import Serializers as MonitorSerializers
from django_prefixctl.rest.serializers.prefixctl import Serializers, DeletePrefixSetsSerializer
from django_prefixctl.rest.views.monitor import (
    add_monitor,
    list_monitors,
    remove_monitor,
)


@route
class PrefixSet(CachedObjectMixin, SlugObjectMixin, viewsets.GenericViewSet):
    """
    ViewSet for handling PrefixSet operations.

    Arguments:
    - request: The HTTP request object.
    - org: The organization object.
    - instance: The instance associated with the PrefixSet.
    - pk: The primary key of the PrefixSet.
    """

    serializer_class = Serializers.prefix_set
    queryset = models.PrefixSet.objects.all()
    schema = PrefixSetSchema()

    def get_serializer_dynamic(self, path, method, direction):
        """
        Dynamically selects a serializer based on the request path and method.

        Arguments:
        - path: The request path.
        - method: The HTTP method of the request.
        - direction: The direction of serialization (request/response).
        """
        if "delete_monitor" in path:
            if direction == "response":
                return MonitorSerializers.prefix_monitor()
            else:
                return Serializers.prefix_set_monitor_selector()

        if "delete_prefix" in path:
            if direction == "response":
                return Serializers.prefix()

        return self.get_serializer()

    @action(
        detail=False,
        methods=["GET"],
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def search_prefix(self, request, org, instance, *args, **kwargs):
        """
        Searches for a prefix based on the provided query parameter.

        Arguments:
        - request: The HTTP request object, containing the query parameter 'q'.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        search_term = request.query_params.get("q", "")
        prefixes = models.Prefix.objects.filter(prefix__startswith=search_term)

        serializer = Serializers.prefix(prefixes, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def search_prefixset(self, request, org, instance, *args, **kwargs):
        """
        Searches for a prefixset based on the provided query parameter.

        Arguments:
        - request: The HTTP request object, containing the query parameter 'q'.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        search_term = request.query_params.get("q", "")
        prefixsets = instance.prefix_set_set.filter(name__icontains=search_term)

        serializer = Serializers.prefix_set(prefixsets, many=True)
        return Response(serializer.data)

    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        """
        Lists all PrefixSets for the given instance.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        serializer = Serializers.prefix_set(
            instance.prefix_set_set.all().order_by("-created"), many=True
        )
        return Response(serializer.data)

    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def retrieve(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Retrieves a single PrefixSet based on the primary key.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        prefix_set = self.get_object()
        serializer = self.serializer_class(prefix_set)
        return Response(serializer.data)

    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def create(self, request, org, instance, *args, **kwargs):
        """
        Creates a new PrefixSet with the data provided in the request.

        Arguments:
        - request: The HTTP request object containing the PrefixSet data.
        - org: The organization object.
        - instance: The instance for which the PrefixSet will be created.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        serializer = self.serializer_class(
            data=request.data, context={"instance": instance}
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        prefix_set = serializer.save()

        return Response(self.serializer_class(prefix_set).data)

    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def update(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Updates an existing PrefixSet with the data provided in the request.

        Arguments:
        - request: The HTTP request object containing the updated PrefixSet data.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet to update.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        data["instance"] = instance.id
        serializer = self.serializer_class(instance=self.get_object(), data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        serializer.save()
        return Response(serializer.data)

    @load_object("prefix_set", models.PrefixSet, id="pk", instance="instance")
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def destroy(self, request, org, instance, prefix_set, pk=None, *args, **kwargs):
        """
        Deletes a PrefixSet based on the primary key.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - prefix_set: The PrefixSet object to delete.
        - pk: The primary key of the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = self.serializer_class(prefix_set).data
        prefix_set.delete()
        return Response(data)

    # List / Add / Remove Monitors

    @action(detail=True, methods=["GET"])
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def monitors(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Lists all monitors associated with a PrefixSet.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        prefix_set = self.get_object()
        monitors = list_monitors(instance, prefix_set=prefix_set)
        return Response(monitors)

    @action(detail=True, methods=["POST"])
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def add_monitor(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Adds a monitor to a PrefixSet.

        Arguments:
        - request: The HTTP request object containing the monitor data.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet to which the monitor will be added.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        data["prefix_set"] = self.get_object().id
        return add_monitor(request, instance, data)

    @action(
        detail=True,
        methods=["DELETE"],
        serializer_class=MonitorSerializers.delete_monitor,
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def delete_monitor(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Deletes a monitor from a PrefixSet.

        Arguments:
        - request: The HTTP request object containing the monitor data.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet from which the monitor will be deleted.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        return remove_monitor(request, instance, request.data)

    # Add / Remove Prefixes

    @action(detail=True, methods=["GET"])
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def prefixes(self, request, org, instance, pk=None, *args, **kwargs):
        prefix_set = self.get_object()

        serializer = Serializers.prefix(prefix_set.prefix_set.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"], serializer_class=Serializers.prefix)
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def add_prefix(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Adds a prefix to a PrefixSet.

        Arguments:
        - request: The HTTP request object containing the prefix data.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet to which the prefix will be added.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        data["prefix_set"] = self.get_object().id

        serializer = Serializers.prefix(data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        prefix = serializer.save()
        return Response(Serializers.prefix(prefix).data)

    @action(
        detail=True,
        methods=["DELETE"],
        serializer_class=Serializers.prefix_set_prefix_selector,
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def delete_prefix(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Deletes a prefix from a PrefixSet.

        Arguments:
        - request: The HTTP request object containing the prefix ID to delete.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet from which the prefix will be deleted.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        prefix_set = self.get_object()
        prefix = models.Prefix.objects.get(prefix_set=prefix_set, pk=data.get("id"))

        response = Response(Serializers.prefix(prefix).data)

        prefix.delete()

        return response

    
    @action(
        detail=False,
        methods=["POST"],
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def delete_prefixes(self, request, org, instance, *args, **kwargs):
        """
        Delete all prefixSets older than the given days.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the PrefixSets.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        serializer = DeletePrefixSetsSerializer(data=request.data)
        if serializer.is_valid():
            days = serializer.validated_data['days']
            cutoff_date = timezone.now() - timedelta(days=days)
            instance_prefix_sets = instance.prefix_set_set.filter(created__lt=cutoff_date)

            for prefix_set in instance_prefix_sets:
                prefix_set.delete()

            return Response({"success": True})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(
        detail=True, methods=["POST"], serializer_class=Serializers.bulk_create_prefixes
    )
    @grainy_endpoint(namespace="prefix_set.{request.org.permission_id}")
    def add_prefixes(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Adds multiple prefixes to a PrefixSet.

        Arguments:
        - request: The HTTP request object containing the prefixes data.
        - org: The organization object.
        - instance: The instance associated with the PrefixSet.
        - pk: The primary key of the PrefixSet to which the prefixes will be added.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        data = request.data
        data["prefix_set"] = self.get_object().id

        serializer = Serializers.bulk_create_prefixes(data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        prefixes = serializer.save()

        return Response(Serializers.prefix(prefixes, many=True).data)


@route
class ASNSet(CachedObjectMixin, SlugObjectMixin, viewsets.GenericViewSet):
    """
    ViewSet for handling ASNSet operations.

    Arguments:
    - request: The HTTP request object.
    - org: The organization object.
    - instance: The instance associated with the ASNSet.
    - pk: The primary key of the ASNSet.
    """

    serializer_class = Serializers.asn_set
    queryset = models.ASNSet.objects.all()
    schema = ASNSetSchema()

    def get_serializer_dynamic(self, path, method, direction):
        """
        Dynamically selects a serializer based on the request path and method.

        Arguments:
        - path: The request path.
        - method: The HTTP method of the request.
        - direction: The direction of serialization (request/response).
        """
        if "delete_monitor" in path:
            if direction == "response":
                return MonitorSerializers.asn_monitor()
            else:
                return Serializers.asn_set_monitor_selector()

        if "delete_asn" in path:
            if direction == "response":
                return Serializers.asn()

        return self.get_serializer()

    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        """
        Lists all ASNSets for the given instance.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        serializer = Serializers.asn_set(instance.asn_set_set.all(), many=True)
        return Response(serializer.data)

    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def retrieve(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Retrieves a single ASNSet based on the primary key.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        asn_set = self.get_object()
        serializer = self.serializer_class(asn_set)
        return Response(serializer.data)

    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def create(self, request, org, instance, *args, **kwargs):
        """
        Creates a new ASNSet with the data provided in the request.

        Arguments:
        - request: The HTTP request object containing the ASNSet data.
        - org: The organization object.
        - instance: The instance for which the ASNSet will be created.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        serializer = self.serializer_class(
            data=request.data, context={"instance": instance}
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        asn_set = serializer.save()

        return Response(self.serializer_class(asn_set).data)

    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def update(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Updates an existing ASNSet with the data provided in the request.

        Arguments:
        - request: The HTTP request object containing the updated ASNSet data.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet to update.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        data["instance"] = instance.id
        serializer = self.serializer_class(instance=self.get_object(), data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        serializer.save()
        return Response(serializer.data)

    @load_object("asn_set", models.ASNSet, id="pk", instance="instance")
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def destroy(self, request, org, instance, asn_set, pk=None, *args, **kwargs):
        """
        Deletes an ASNSet based on the primary key.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - asn_set: The ASNSet object to delete.
        - pk: The primary key of the ASNSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = self.serializer_class(asn_set).data
        asn_set.delete()
        return Response(data)

    @action(detail=True, methods=["GET"])
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def asns(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Lists all ASNs within an ASNSet.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        asn_set = self.get_object()

        serializer = Serializers.asn(asn_set.asn_set.all(), many=True)

        return Response(serializer.data)

    @action(detail=True, methods=["POST"], serializer_class=Serializers.asn)
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def add_asn(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Adds an ASN to an ASNSet.

        Arguments:
        - request: The HTTP request object containing the ASN data.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet to which the ASN will be added.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        data = request.data
        data["asn_set"] = self.get_object().id

        serializer = Serializers.asn(data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        asn = serializer.save()
        return Response(Serializers.asn(asn).data)

    @action(
        detail=True,
        methods=["DELETE"],
        serializer_class=Serializers.asn_set_asn_selector,
    )
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def delete_asn(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Deletes an ASN from an ASNSet.

        Arguments:
        - request: The HTTP request object containing the ASN to be deleted.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet from which the ASN will be deleted.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        data = request.data

        asn_set = self.get_object().id
        asn = models.ASN.objects.get(asn_set=asn_set, asn=data["asn"])

        response_data = Serializers.asn(asn).data

        asn.delete()

        return Response(response_data)

    # List / Add / Remove Monitors

    @action(detail=True, methods=["GET"])
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def monitors(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Lists all monitors associated with an ASNSet.

        Arguments:
        - request: The HTTP request object.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        asn_set = self.get_object()
        monitors = list_monitors(instance, asn_set=asn_set)
        return Response(monitors)

    @action(detail=True, methods=["POST"])
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def add_monitor(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Adds a monitor to an ASNSet.

        Arguments:
        - request: The HTTP request object containing the monitor data.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet to which the monitor will be added.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """
        data = request.data
        data["asn_set"] = self.get_object().id
        return add_monitor(request, instance, data)

    @action(
        detail=True,
        methods=["DELETE"],
        serializer_class=MonitorSerializers.delete_monitor,
    )
    @grainy_endpoint(namespace="asn_set.{request.org.permission_id}")
    def delete_monitor(self, request, org, instance, pk=None, *args, **kwargs):
        """
        Removes a monitor from an ASNSet.

        Arguments:
        - request: The HTTP request object containing the monitor data.
        - org: The organization object.
        - instance: The instance associated with the ASNSet.
        - pk: The primary key of the ASNSet from which the monitor will be removed.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.
        """

        return remove_monitor(request, instance, request.data)
