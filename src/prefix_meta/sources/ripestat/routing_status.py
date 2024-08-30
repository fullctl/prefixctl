import ipaddress
from datetime import datetime, timedelta

import ripestat
import ripestat.stat.routing_status
from django.utils import timezone

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

    def seen_in_routing_tables(self, now: datetime) -> list[dict]:
        # main prefix
        more_specifics = self.data.get("last_seen")

        seen = []
        seen.append(self.prefix_seen(more_specifics, self.prefix, now))

        # more specifics
        for more_specifics in self.data.get("more_specifics", []):
            seen.append(
                {
                    "prefix": more_specifics["prefix"],
                    "seen": True,
                    "more_specific": True,
                    "last_seen": self.date,
                }
            )

        return seen

    def prefix_seen(self, last_seen: dict, prefix: str, date: datetime):

        if not last_seen:
            return {
                "prefix": prefix,
                "seen": False,
                "more_specific": False,
                "last_seen": None,
            }

        seen_dtime = datetime.strptime(last_seen["time"], "%Y-%m-%dT%H:%M:%S")
        # set timezone to UTC
        seen_dtime = seen_dtime.replace(tzinfo=timezone.utc)
        # if time difference is less than 24 hours we consider it as seen

        seen = False
        if date - seen_dtime < timedelta(hours=24):
            seen = True

        return {
            "prefix": prefix,
            "seen": seen,
            "more_specific": False,
            "last_seen": seen_dtime,
        }


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

        data["more_specifics"] = data.get("more_specifics", [])

        yield date, target, data
