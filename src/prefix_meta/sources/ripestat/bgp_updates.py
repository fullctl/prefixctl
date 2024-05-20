import datetime

import ripestat
import ripestat.stat.bgp_updates
import ripestat.stat.rpki_validation_status

from .base import RipestatData, RipestatRequest

__all__ = [
    "BgpUpdates",
    "BgpUpdatesData",
]


class BgpUpdatesData(RipestatData):
    class Meta:
        proxy = True

    class Config(RipestatData.Config):
        type = "bgp"
        source_name = "ripestat-bgpupdates"

    @property
    def recent_bgp_update(self):
        try:
            return self.data.get("updates", [])[-1]
        except IndexError:
            return {}

    def seen_on_routing_tables(self, dt):
        recent = self.recent_bgp_update
        if not recent:
            return False

        seen_dt = datetime.datetime.strptime(
            recent["timestamp"], "%Y-%m-%dT%H:%M:%S"
        ).replace(tzinfo=datetime.timezone.utc)

        return seen_dt >= dt


class BgpUpdates(RipestatRequest):
    class Meta:
        proxy = True

    class Config(RipestatRequest.Config):
        ripestat_path = ripestat.stat.bgp_updates.BGPUpdates.PATH
        source_name = "ripestat-bgpupdates"
        meta_data_cls = BgpUpdatesData
        cache_expiry = 3600 * 6

    @classmethod
    def ripestat_request(cls, target):
        ripe = ripestat.RIPEstat()
        return ripe.bgp_updates(target, None)
