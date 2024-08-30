from datetime import datetime

import ripestat
import ripestat.stat.historical_whois

from .base import RipestatData, RipestatRequest

__all__ = ["RIRStatsCountry", "RIRStatsCountryData"]


class RIRStatsCountryData(RipestatData):
    class Meta:
        proxy = True

    class Config(RipestatData.Config):
        type = "location"
        source_name = "ripestat-rirstatscountry"

    @property
    def country(self):
        try:
            return self.data["locations"][0]["country"]
        except (KeyError, IndexError):
            return None

    @property
    def countries(self):
        for loc in self.data.get("locations", []):
            yield loc["country"]

    @property
    def query_time(self):
        try:
            t = self.data["query_time"]
            t = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            return t
        except KeyError:
            return None


class RIRStatsCountry(RipestatRequest):
    class Meta:
        proxy = True

    class Config(RipestatRequest.Config):
        ripestat_path = ripestat.stat.rir_stats_country.RIRStatsCountry.PATH
        source_name = "ripestat-rirstatscountry"
        meta_data_cls = RIRStatsCountryData

    @classmethod
    def ripestat_request(cls, target):
        ripe = ripestat.RIPEstat()
        return ripe.rir_stats_country(target)

    def prepare_data(self, data):
        """
        Normalize the data
        """

        normalized = {
            "query_time": data["parameters"]["query_time"],
            "locations": [],
        }

        for res in data.get("located_resources", []):
            normalized["locations"].append(
                {"country": res["location"], "prefix": res["resource"]}
            )

        return normalized
