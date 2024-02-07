from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer

import django_prefixctl.models.prefixctl as models

# from rest_framework import serializers


Serializers, register = serializer_registry()


@register
class Prefix(ModelSerializer):
    """
    Serializer for Prefix model.

    Provides serialization and deserialization for Prefix instances, allowing
    manipulation of prefix data.
    """

    class Meta:
        """
        Meta class for Prefix serializer to specify model and fields to include.
        """

        model = models.Prefix
        fields = [
            "prefix",
            "mask_length_range",
        ]


@register
class PrefixSet(ModelSerializer):
    """
    Serializer for PrefixSet model.

    Provides serialization and deserialization for PrefixSet instances, enabling
    management and linkage of multiple prefix instances.
    """

    prefixes = Prefix(source="prefix_set", many=True, read_only=True)

    class Meta:
        """
        Meta class for PrefixSet serializer to specify model and fields to include.
        """

        model = models.PrefixSet
        fields = [
            "instance",
            "name",
            "description",
            "prefixes",
        ]
