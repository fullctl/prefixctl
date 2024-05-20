import ripestat
import ripestat.stat.historical_whois

from .base import RipestatData, RipestatRequest

__all__ = ["RIR", "RIRData"]


class RIRData(RipestatData):
    class Meta:
        proxy = True

    class Config(RipestatData.Config):
        type = "rir"
        source_name = "ripestat-rir"

    @property
    def rirs(self):
        for rir in self.data.get("rirs", []):
            yield rir["rir"]

    @property
    def count(self):
        return len([r for r in self.rirs])


class RIR(RipestatRequest):
    class Meta:
        proxy = True

    class Config(RipestatRequest.Config):
        ripestat_path = ripestat.stat.rir.RIR.PATH
        source_name = "ripestat-rir"
        meta_data_cls = RIRData

    @classmethod
    def ripestat_request(cls, target):
        ripe = ripestat.RIPEstat()
        return ripe.rir(target)  # type: ignore
