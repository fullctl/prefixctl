import ipaddress

import ripestat
import ripestat.stat.routing_status

from .base import RipestatData, RipestatRequest

__all__ = [
    "RoutingStatus",
    "RoutingStatusData",
]


class RoutingStatusData(RipestatData):
    class Meta:
        proxy = True

    class Config(RipestatData.Config):
        type = "route"
        source_name = "ripestat-routingstatus"

    @property
    def origin_asn(self):
        try:
            return self.data["last_seen"]["origin"]
        except KeyError:
            return None

    @property
    def rpki_status(self):
        return self.data.get("rpki_status", {}).get("status", "unknown")

    @property
    def announced_prefixes(self):
        for row in self.data.get("announced_prefixes", []):
            yield ipaddress.ip_network(row["prefix"])


class RoutingStatus(RipestatRequest):
    class Meta:
        proxy = True

    class Config(RipestatRequest.Config):
        ripestat_path = ripestat.stat.routing_status.RoutingStatus.PATH
        source_name = "ripestat-routingstatus"
        meta_data_cls = RoutingStatusData
        cache_expiry = 12 * 3600

    @classmethod
    def ripestat_request(cls, target):
        ripe = ripestat.RIPEstat()
        return ripe.routing_status(target)

    def process_response(self, response, target, date):
        data = response.data

        try:
            origin_asn = int(data.get("last_seen", {}).get("origin"))
        except (ValueError, TypeError):
            origin_asn = None

        if origin_asn:
            # Get RPKI status here since we do not have a way
            # to store ASN meta yet, but still want to cache the request

            ripe = ripestat.RIPEstat()
            rpki_satus = ripe.rpki_validation_status(origin_asn, target)

            data["rpki_status"] = rpki_satus.data

            # Get annouced prefixes here since we do not have a way
            # to store ASN meta yet, but still want to cache the request

            announced_prefixes = ripe.announced_prefixes(origin_asn)
            data["announced_prefixes"] = announced_prefixes.data["prefixes"]

        yield date, target, data
