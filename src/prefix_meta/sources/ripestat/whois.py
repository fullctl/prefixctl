import ripestat
import ripestat.stat.historical_whois

from .base import RipestatData, RipestatRequest

__all__ = [
    "HistoricalWhois",
]


class HistoricalWhoisData(RipestatData):
    class Meta:
        proxy = True

    class Config(RipestatData.Config):
        type = "whois"
        source_name = "ripestat-historicalwhois"


class HistoricalWhois(RipestatRequest):
    class Meta:
        proxy = True

    class Config(RipestatRequest.Config):
        ripestat_path = ripestat.stat.historical_whois.HistoricalWhois.PATH
        source_name = "ripestat-historicalwhois"
        meta_data_cls = HistoricalWhoisData

    @classmethod
    def ripestat_request(cls, target):
        ripe = ripestat.RIPEstat()
        return ripe.historical_whois(target, None)

    def prepare_data(self, data):
        """
        Normalize the data
        """

        normalized = {}
        references = {}

        for ref in data.get("referencing", []):
            references[ref[0]["key"]] = ref[0]["type"]

        for obj in data.get("objects", []):
            normalized[obj["key"]] = _obj = {
                "version": obj["version"],
                "type": obj["type"],
            }
            for attrib in obj.get("attributes"):
                name = attrib["attribute"].replace("-", "_")

                if name == "mnt_by":
                    _obj.setdefault("mnt_by", [])
                    _obj[name].append(attrib["value"])
                else:
                    _obj[name] = attrib["value"]

                if attrib["attribute"] in ["admin-c", "tech-c", "abuse-c"]:
                    _obj[f"{name}_type"] = references[attrib["value"]]

        return normalized
