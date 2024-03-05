from django.utils.translation import gettext_lazy as _
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer
from rest_framework import serializers

import django_prefixctl.models as models

Serializers, register = serializer_registry()

MONITOR_CLASSES = {}
PREFIX_MONITOR_CLASSES = {}
ASN_MONITOR_CLASSES = {}


def register_prefix_monitor(cls):
    """
    Registers a class as a prefix monitor.

    Arguments:
    cls: The class to register as a monitor.

    Returns:
    The class itself after registration.
    """
    PREFIX_MONITOR_CLASSES[cls.ref_tag] = cls
    MONITOR_CLASSES[cls.ref_tag] = cls
    return cls


def register_asn_monitor(cls):
    """
    Registers a class as an ASN monitor.

    Arguments:
    cls: The class to register as a monitor.

    Returns:
    The class itself after registration.
    """
    ASN_MONITOR_CLASSES[cls.ref_tag] = cls
    MONITOR_CLASSES[cls.ref_tag] = cls
    return cls


def get_monitor_class(type):
    """
    Retrieves the monitor class based on the given type.

    Arguments:
    type: The type of monitor to retrieve.

    Returns:
    The class of the specified monitor type.
    """
    print("MONITORS", MONITOR_CLASSES)
    return MONITOR_CLASSES[type]


class MonitorConfigSerializerField(serializers.Field):
    """
    Custom field that can take any of the monitor config serializers
    """

    def to_internal_value(self, data):
        """
        Converts the input data into a validated and deserialized format.

        Arguments:
        data: The input data to be processed.

        Returns:
        The validated data after processing.

        Raises:
        ValidationError: If the monitor type is invalid or other validation fails.
        """
        try:
            typ = self.parent.initial_data["type"]
        except KeyError:
            return data

        serializer_class = get_monitor_class(typ)
        if not serializer_class:
            raise serializers.ValidationError({"type": "Invalid monitor type."})

        monitor_instance = self.parent.context.get("monitor_instance")

        serializer = serializer_class(data=data, instance=monitor_instance)

        if serializer.is_valid(raise_exception=True):
            return serializer.validated_data

    def to_representation(self, value):
        """
        Converts the instance into the native Python datatype.

        Arguments:
        value: The value to be converted.

        Returns:
        The converted value.
        """
        if not hasattr(self.parent, "initial_data"):
            return value

        typ = self.parent.initial_data["type"]
        serializer_class = get_monitor_class(typ)
        serializer = serializer_class(value)
        return serializer.data


class MonitorCreationMixin:
    """
    Mixin that overrides the create method to set
    the instance on the monitor from context
    """

    @property
    def grainy_namespace(self):
        monitor_serializer = get_monitor_class(self.validated_data["monitor_type"])
        org = self.context.get("instance").org
        return (
            monitor_serializer.Meta.model.Grainy.namespace() + f".{org.permission_id}"
        )

    def create(self, validated_data, **kwargs):
        """
        Creates a new monitor instance using the provided validated data.

        Arguments:
        validated_data: The dictionary of validated data to use for creating the monitor.
        **kwargs: Additional keyword arguments.

        Returns:
        The newly created monitor instance.
        """
        validated_data["instance"] = self.context.get("instance")

        try:
            validated_data.pop("monitor_type")
        except KeyError:
            pass

        return super().create(validated_data, **kwargs)


@register_asn_monitor
@register
class ASNMonitor(MonitorCreationMixin, ModelSerializer):
    asn_set_name = serializers.SerializerMethodField()
    instance = serializers.PrimaryKeyRelatedField(read_only=True)
    monitor_type = serializers.ChoiceField(
        choices=["asn_monitor"], default="asn_monitor"
    )

    class Meta:
        model = models.ASNMonitor
        fields = [
            "instance",
            "asn_set",
            "asn_set_name",
            "new_prefix_detection",
            "monitor_type",
        ]

    def get_asn_set_name(self, obj):
        return obj.asn_set.name

    def validate(self, data):
        # validate_shared_instance(**data)
        return data


@register
class DeleteMonitor(serializers.Serializer):
    """
    Serializer for deleting a monitor
    """

    id = serializers.IntegerField(help_text=_("Monitor id"))
    monitor_type = serializers.ChoiceField(choices=MONITOR_CLASSES)
    ref_tag = "delete_monitor"

    def delete(self, validated_data):
        monitor = self.context.get("monitor_instance")
        if not monitor:
            raise serializers.ValidationError("Monitor instance not found")
        monitor.delete()

    class Meta:
        fields = ["id", "monitor_type"]
