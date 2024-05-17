from django.utils.translation import gettext_lazy as _
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.fields import DynamicChoiceField
from fullctl.django.rest.serializers import ModelSerializer, SlugSerializerMixin
from fullctl.django.validators import validate_alphanumeric, validate_alphanumeric_list
from rest_framework import serializers

import django_prefixctl.models as models
from django_prefixctl.rest.serializers.monitor import (
    PREFIX_MONITOR_CLASSES,
)
from django_prefixctl.rest.views.monitor import list_monitors

Serializers, register = serializer_registry()


def validate_shared_instance(instance, **children):
    """
    Validates that the instance associated with each child is the same.

    Arguments:
    instance: The primary instance to match against.
    **children: Keyword arguments representing each child object.

    Raises:
    ValidationError: If any child's instance does not match the primary instance.
    """
    for name, child in children.items():
        other = getattr(child, "instance", None)
        if isinstance(other, Instance) and other != instance:
            raise serializers.ValidationError({name: ["instance mismatch"]})


@register
class Instance(ModelSerializer):
    class Meta:
        model = models.Instance
        fields = []


@register
class Prefix(ModelSerializer):
    mask_length_range = serializers.CharField(
        required=False,
        allow_blank=True,
        default="exact",
    )

    def validate_mask_length_range(self, val):
        """
        Validates the mask length range input.

        Arguments:
        val: The value of the mask length range to validate.

        Returns:
        The validated mask length range value. Defaults to 'exact' if input is empty.
        """

        return "exact" if not val else val

    class Meta:
        model = models.Prefix
        fields = [
            "prefix_set",
            "prefix",
            "mask_length_range",
        ]


@register
class PrefixSet(SlugSerializerMixin, ModelSerializer):
    prefixes = Prefix(source="prefix_set", many=True, read_only=True)
    monitors = serializers.SerializerMethodField()
    instance = serializers.PrimaryKeyRelatedField(read_only=True)

    irr_as_set = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            validate_alphanumeric,
        ],
    )

    irr_sources = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            validate_alphanumeric_list,
        ],
    )

    num_monitors = serializers.SerializerMethodField()
    num_prefixes = serializers.SerializerMethodField()

    class Meta:
        model = models.PrefixSet
        fields = [
            "instance",
            "name",
            "slug",
            "description",
            "prefixes",
            "monitors",
            "irr_import",
            "irr_as_set",
            "irr_sources",
            "irr_import_status",
            "num_monitors",
            "num_prefixes",
            "ux_keep_list_open",
        ]

    def get_num_monitors(self, obj):
        """
        Gets the number of monitors associated with the PrefixSet.

        Arguments:
        obj: The PrefixSet instance.

        Returns:
        The count of associated monitors.
        """
        cnt = 0
        for moncls in PREFIX_MONITOR_CLASSES.values():
            cnt += moncls.Meta.model.objects.filter(prefix_set=obj).count()
        return cnt

    def get_num_prefixes(self, obj):
        """
        Gets the number of prefixes associated with the PrefixSet.

        Arguments:
        obj: The PrefixSet instance.

        Returns:
        The count of associated prefixes.
        """
        return obj.prefix_set.count()

    def get_monitors(self, obj):
        """
        Retrieves a list of monitors associated with the PrefixSet.

        Arguments:
        obj: The PrefixSet instance.

        Returns:
        A list of monitor instances associated with the PrefixSet.
        """
        return list_monitors(obj.instance, prefix_set=obj)

    def validate(self, data):
        # if irr_import is enabled, make sure irr_as_set is set

        if data.get("irr_import") and not data.get("irr_as_set"):
            raise serializers.ValidationError(
                {"irr_as_set": ["AS-SET required when IRR import is enabled"]}
            )

        return data

    def create(self, validated_data, **kwargs):
        validated_data["instance"] = self.context.get("instance")
        return super().create(validated_data, **kwargs)


@register
class BulkCreatePrefixes(serializers.Serializer):

    """
    Allows adding of many prefixes at once
    """

    prefixes = serializers.ListField(
        child=serializers.CharField(),
        help_text=_("List of prefixes to add"),
    )
    prefix_set = serializers.PrimaryKeyRelatedField(
        queryset=models.PrefixSet.objects.all(),
        help_text=_("Prefix set to add prefixes to"),
    )

    ref_tag = "bulk_create_prefixes"

    class Meta:
        fields = ["prefixes", "prefix_set"]

    def save(self):
        prefix_set = self.validated_data["prefix_set"]
        for prefix in self.validated_data["prefixes"]:
            models.Prefix.objects.get_or_create(prefix_set=prefix_set, prefix=prefix)


@register
class ASN(ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.ASN
        fields = [
            "asn_set",
            "asn",
            "name",
        ]

    def get_name(self, obj):
        try:
            return obj.pdb.name
        except Exception:
            return ""


@register
class ASNSet(SlugSerializerMixin, ModelSerializer):
    asns = ASN(source="asn_set", many=True, read_only=True)
    monitors = serializers.SerializerMethodField()
    instance = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.ASNSet
        fields = [
            "instance",
            "name",
            "slug",
            "description",
            "asns",
            "monitors",
        ]

    def get_monitors(self, obj):
        return list_monitors(obj.instance, asn_set=obj)

    def create(self, validated_data, **kwargs):
        validated_data["instance"] = self.context.get("instance")
        return super().create(validated_data, **kwargs)


@register
class ASNSetASNSelector(serializers.Serializer):
    asn = serializers.IntegerField(help_text=_("ASN"))

    ref_tag = "asn_set_asn_selector"

    class Meta:
        fields = ["asn"]


@register
class ASNSetMonitorSelector(serializers.Serializer):
    monitor_type = DynamicChoiceField(
        choices=lambda: ["origin"], help_text=_("Monitor type name")
    )
    id = serializers.IntegerField(help_text=_("Monitor id"))

    ref_tag = "asn_set_monitor_selector"

    class Meta:
        fields = ["id", "monitor_type"]


@register
class PrefixSetPrefixSelector(serializers.Serializer):
    id = serializers.IntegerField(help_text=_("Prefix id"))

    ref_tag = "prefix_set_prefix_selector"

    class Meta:
        fields = ["id"]


@register
class PrefixSetMonitorSelector(serializers.Serializer):
    monitor_type = DynamicChoiceField(
        choices=lambda: PREFIX_MONITOR_CLASSES.keys(), help_text=_("Monitor type name")
    )
    id = serializers.IntegerField(help_text=_("Monitor id"))

    ref_tag = "prefix_set_monitor_selector"

    class Meta:
        fields = ["id", "monitor_type"]


@register
class AlertGroup(ModelSerializer):
    class Meta:
        model = models.AlertGroup
        fields = [
            "instance",
            "name",
        ]


@register
class AlertRecipient(ModelSerializer):
    class Meta:
        model = models.AlertRecipient
        fields = [
            "alertgrp",
            "typ",
            "recipient",
        ]


class DeletePrefixesSerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=0, required=True)

    class Meta:
        fields = ["days"]
