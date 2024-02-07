from rest_framework import serializers
from fullctl.django.rest.serializers import ModelSerializer
from fullctl.django.rest.decorators import serializer_registry
from django_prefixctl.rest.serializers.monitor import (
    register_prefix_monitor,
    MonitorCreationMixin,
)

import monitor_example.models as models

Serializers, register = serializer_registry()


# register the monitor with prefixctl
@register_prefix_monitor
# add the monitor to the serializer registry, afterwards it
# will be available as Serializers.example_monitor, purely for convenience
@register
class ExampleMonitor(MonitorCreationMixin, ModelSerializer):

    """
    A bare minimum monitor REST serializer for our example monitor.
    """

    # set the monitor type choices and default
    # to the reference tag of the monitor model
    monitor_type = serializers.ChoiceField(
        choices=["example_monitor"], default="example_monitor"
    )
    instance = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.ExampleMonitor
        fields = [
            "instance",
            "prefix_set",
            "monitor_type",
        ]
