import rdap
import rdap.exceptions

from prefix_meta.models import Data, Request

__all__ = [
    "RdapData",
    "RdapRequest",
]

import structlog

logger = structlog.get_logger(__name__)


class RdapData(Data):
    class Meta:
        proxy = True

    class Config(Data.Config):
        source_name = "rdap"
        type = "rdap"


class RdapRequest(Request):
    class Meta:
        proxy = True

    class Config(Request.Config):
        source_name = "rdap"
        meta_data_cls = RdapData
        max_prefixlen_4 = 10
        max_prefixlen_6 = 32
        min_prefixlen_4 = 32
        min_predixlen_6 = 128

        cache_expiry = 86400

        rdap_url = None

    @classmethod
    def target_to_url(cls, target):
        return f"RDAP {target}"

    @classmethod
    def target_to_type(cls, target):
        return "live"

    @classmethod
    def send(cls, target):
        url = cls.target_to_url(target)
        logger.debug(f"sending request to {url} - target - {target}")
        data = cls.rdap_request(target)
        return cls.process(target, url, 200, data)

    @classmethod
    def rdap_request(cls, target):
        client = rdap.RdapClient()
        try:
            data = client.get(f"{target}")
        except rdap.exceptions.RdapNotFoundError:
            return {}

        inetnum = f"{data.data.get('startAddress')} - {data.data.get('endAddress')}"

        r_data = {inetnum: {}}

        keys = ["org_name", "org_address", "handle", "name", "kind", "emails"]

        for key in keys:
            try:
                r_data[inetnum].update({key: getattr(data, key)})
            except (KeyError, AttributeError):
                continue

        rir_name = data.get_rir()
        r_data[inetnum]["source"] = rir_name.upper() if rir_name else None

        for event in data.data.get("events", []):
            if event["eventAction"] == "last changed":
                r_data[inetnum]["last_changed"] = event["eventDate"]
            elif event["eventAction"] == "registration":
                r_data[inetnum]["registration"] = event["eventDate"]

        return r_data
