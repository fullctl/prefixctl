import ipaddress

import fullctl.django.models.abstract.meta as meta
from django.db import models
from django.utils.translation import gettext_lazy as _
from netfields import CidrAddressField, NetManager


class Data(meta.Data):

    """
    Normalized prefix meta data storage
    """

    prefix = CidrAddressField()

    objects = NetManager()

    class Meta:
        db_table = "prefix_meta_data"
        verbose_name_plural = _("Meta data")
        verbose_name = _("Meta data")
        indexes = [
            models.Index("prefix", name="prefix_idx"),
            models.Index("source_name", name="source_name_idx"),
            models.Index("date", name="date_idx"),
            models.Index("type", name="type_idx"),
            models.Index(fields=["prefix", "type", "date"], name="prefix_type_idx"),
        ]

    class HandleRef:
        tag = "prefix_meta_data"

    @classmethod
    def get_prefix_queryset(cls, prefix):
        return (
            cls.objects.filter(
                models.Q(prefix__net_contained_or_equal=prefix)
                | models.Q(subnets__prefix__net_contains_or_equals=prefix)
            )
            .order_by("-date", "prefix")
            .distinct("date", "prefix")
        )

    @property
    def get_matched_subnets(self):
        return
        yield

    @property
    def matched_subnet_count(self):
        return self.subnets.all().count()

    @property
    def source(self):
        return self.source_name.split("-")[0]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.subnets.all().delete()

        DataSubnet.objects.bulk_create(
            [
                DataSubnet(prefix=prefix, meta_data=self)
                for prefix in {p for p in self.get_matched_subnets}
            ]
        )


class DataSubnet(models.Model):

    """
    Indicates that a specific subnet has a match
    in the parent prefix meta data
    """

    prefix = CidrAddressField()
    meta_data = models.ForeignKey(
        Data, related_name="subnets", on_delete=models.CASCADE
    )

    objects = NetManager()

    class Meta:
        db_table = "prefix_meta_data_subnet"
        verbose_name = _("Subnet match")
        verbose_name_plural = _("Subnet matches")
        indexes = [
            models.Index("prefix", name="subnet_prefix_idx"),
            models.Index("meta_data_id", name="subnet_meta_data_id_idx"),
        ]

    class HandleRef:
        tag = "prefix_meta_data_subnet"


class Response(meta.Response):

    """
    Maintains a cache for third party data responses
    """

    request = models.OneToOneField(
        "prefix_meta.Request",
        on_delete=models.CASCADE,
        related_name="response",
    )

    class Meta:
        db_table = "prefix_meta_response"
        verbose_name_plural = _("Response cache")
        verbose_name = _("Response cache")

    class HandleRef:
        tag = "prefix_meta_response"

    class Config:
        meta_data_cls = Data


class Request(meta.Request):

    """
    Handles logic for requesting and rate-throttling
    third party meta data for a prefix
    """

    prefix = CidrAddressField()

    objects = NetManager()

    class Config:
        target_field = "prefix"

        cache_expiry = 86400

        # prefixes bigger than this are split into subnets
        # of this size (ipv4 and 6 respetively)
        max_prefixlen_4 = 24
        max_prefixlen_6 = 64

        # prefixes smaller than this will be combined into
        # a super net of this size (ipv4 and 6 respectively)
        min_prefixlen_4 = 24
        min_prefixlen_6 = 64

    class Meta:
        db_table = "prefix_meta_request"
        verbose_name_plural = _("Request cache")
        verbose_name = _("Request cache")

    class HandleRef:
        tag = "prefix_meta_request"

    @classmethod
    def prepare_request(cls, prefixes):
        """
        Takes a single prefix or a list of prefixes
        and prepares them by making sure they are
        ipaddress network objects and also splitting
        them into smaller subnets if they are larger than
        the limit specified in max_prefixlen
        """

        prefixes = super().prepare_request(prefixes)

        prepared_prefixes = []

        # split into subnets or combine into supernets
        # according to min and max prefixlength configuration

        for prefix in prefixes:
            if isinstance(prefix, str):
                prefix = ipaddress.ip_network(prefix)

            max_prefixlen = cls.config(f"max_prefixlen_{prefix.version}")
            min_prefixlen = cls.config(f"min_prefixlen_{prefix.version}")

            if prefix.prefixlen < max_prefixlen:
                prepared_prefixes.extend(list(prefix.subnets(new_prefix=max_prefixlen)))
            elif prefix.prefixlen > min_prefixlen:
                prepared_prefixes.append(prefix.supernet(new_prefix=min_prefixlen))
            else:
                prepared_prefixes.append(prefix)

        # next check for and remove and prefixes that are subnets
        # of other prefixes, since the request for the supernet will
        # contain the result for the subnet naturally.

        final_prefixes = []
        prepared_prefixes = list(set(prepared_prefixes))
        for prefix in prepared_prefixes:
            contained_in_other = False

            for other in prepared_prefixes:
                if prefix != other and prefix.subnet_of(other):
                    contained_in_other = True
                    break

            if not contained_in_other:
                final_prefixes.append(prefix)

        return final_prefixes
