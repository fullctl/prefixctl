import ripestat
import ripestat.stat.historical_whois

from .base import RipestatData, RipestatRequest

__all__ = [
    "HistoricalWhois",
]

NOT_MANAGED_BY_RIPE = "IPv4 address block not managed by the RIPE NCC"

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

        objects = data.get("objects", [])
        is_suggestions = False
        if not objects:
            # no objects, check if there are suggestions
            objects = data.get("suggestions", [])
            is_suggestions = True

        for obj in objects:
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
                    try:
                        _obj[f"{name}_type"] = references[attrib["value"]]
                    except KeyError:
                        pass

        if is_suggestions:
            # for suggestions we only keep the ones where source is RIPE
            # with the idea being that even though its a suggestion
            # RIPEStat has some confidence in it (may need further tweaking)

            # We ignore the ones that state that the IP block is not managed by RIPE

            # We also only keep inetnum suggestions

            normalized = {
                k: v for k, v in normalized.items() 
                if v.get("source") == "RIPE" and 
                v.get("descr") != NOT_MANAGED_BY_RIPE and 
                v.get("type") == "inetnum"
            }

        return normalized
