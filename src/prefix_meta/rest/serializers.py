import ipaddress

from fullctl.django.rest.decorators import serializer_registry

# from fullctl.django.rest.serializers import ModelSerializer
from fullctl.django.rest.serializers.meta import Data
from rest_framework import serializers

import prefix_meta.models as models

Serializers, register = serializer_registry()


@register
class RequestLocation(serializers.Serializer):
    """
    Serializer for triggering a location request for a prefix.
    """

    ref_tag = "request_prefix_location"
    prefixes = serializers.JSONField()

    def validate_prefixes(self, prefixes):
        for prefix in prefixes:
            ipaddress.ip_network(prefix)
        return prefixes


@register
class Location(Data):
    """
    Serializer for location data.
    """

    ref_tag = "prefix_location"

    country_code = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    geo = serializers.SerializerMethodField()
    isp = serializers.SerializerMethodField()

    class Meta(Data.Meta):
        model = models.Data
        fields = [
            "prefix",
            "id",
            "country_code",
            "region",
            "city",
            "geo",
            "isp",
            "data",
        ]

    def get_country_code(self, obj):
        return self.meta_data(obj, "country_code")

    def get_city(self, obj):
        return self.meta_data(obj, "city_name")

    def get_region(self, obj):
        return self.meta_data(obj, "region_name")

    def get_geo(self, obj):
        return {
            "latitude": self.meta_data(obj, "latitude"),
            "longitude": self.meta_data(obj, "longitude"),
        }

    def get_isp(self, obj):
        return self.meta_data(obj, "isp")
