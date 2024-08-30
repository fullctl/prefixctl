"""Provides the Prefix Overview endpoint."""
import ipaddress
from collections import namedtuple
from datetime import datetime
from typing import Optional

from ripestat.validators import Validators


class PrefixOverview:
    """
    This data call gives a summary of the given prefix, including whether and by whom it is announced.

    Reference: `<https://stat.ripe.net/docs/02.data-api/prefix-overview.html>`_
    =========================== =============================================================================================
    Property                    Description
    =========================== =============================================================================================
    ``block``                   This contains information about this ASN or the ASN block it belongs to.
    ``announced``               "True" if the prefix is announced, "False" otherwise
    ``asns``                    A list of ("asn"/"holder") objects representing the originating ASNs.
    ``holder``                  Descriptive name for the AS if AS is given, "null" otherwise
    ``resource``                Outputs the prefix that the query is based on
    ``type``                    For this data call always "prefix"
    ``related_prefixes``        List of related prefixes
    ``actual_num_related``      Total number of (returned and truncated) related prefixes.
    ``num_filtered_out``        Number of prefixes (exact or related) filtered by low-visibility filter. This can be controlled by
                                the parameter "min_peers_seeing".
    ``is_less_specific``        True if the information in the response is for a larger block than the one requested.
    ``resource``                holds the resource this query based on
    ``query_time``              defines the query time the result is based on
    =========================== =============================================================================================

    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()
        prefix_overview = ripe.prefix_overview('193/23')
    """

    PATH = "/prefix-overview"
    VERSION = "1.3"

    def __init__(
        self,
        RIPEstat,
        resource,
        min_peers_seeing: int = None,
        max_related: int = None,
        query_time: Optional[datetime] = None,
    ):
        """
        Initialize and request the prefix overview.

        :param resource: Defines the resource that the query. (This is a prefix (v4/v6))
        :param version: Defines the Minimum number of (RIS) peers necessary to see a resource to
            be included in the result. (if not provided a default is choosen by the server.)
        :param max_related: Limits the number of related prefixes. (if not provided a default is
            choosen by the server.)
        :param query_time: Defines the query time for the lookup. (default latest time data available
            is available for)

        .. code-block:: python
            prefix_overview = ripe.prefix_overview('111/10')
            prefix_overview = ripe.prefix_overview('111.0.0.0/10')
            prefix_overview = ripe.prefix_overview('111/10', max_related=10)
            prefix_overview = ripe.prefix_overview('111/10', min_peers_seeing=10, max_related=10)
            prefix_overview = ripe.prefix_overview('111/10', query_time="2023-02-07T00:00:00")
            prefix_overview = ripe.prefix_overview('111/10', query_time=datetime(2023, 2, 7))
        """
        params = {
            "preferred_version": PrefixOverview.VERSION,
            "resource": str(resource),
        }

        if min_peers_seeing:
            if isinstance(min_peers_seeing, int):
                params["min_peers_seeing"] = str(min_peers_seeing)
            else:
                raise ValueError("min_peers_seeing expected to be int")
        if max_related:
            if isinstance(max_related, int):
                params["max_related"] = str(max_related)
            else:
                raise ValueError("max_related expected to be int")
        if query_time:
            if Validators._validate_datetime(query_time):
                if not isinstance(query_time, datetime):
                    params["query_time"] = query_time
                else:
                    params["query_time"] = query_time.isoformat()
            else:
                raise ValueError("query_time expected to be datetime")

        self._api = RIPEstat._get(PrefixOverview.PATH, params)

    def __repr__(self):
        """Return the resource (IP prefix) and data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource (IP prefix) as string representation of the object."""
        return str(self.resource)

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def block(self):
        """
        This contains information about this ASN or the ASN block it belongs to.
        Keys: desc (a human readable description), name (a human readable name)
            and the referencing resource/resources
        """
        Blocks = namedtuple("Blocks", ["resource", "desc", "name"])
        block = self._api.data["block"]

        resource = ipaddress.ip_network(block["resource"])
        desc = str(block["desc"])
        name = str(block["name"])

        tuple_data = {"resource": resource, "desc": desc, "name": name}

        return Blocks(**tuple_data)

    @property
    def announced(self):
        """True if the prefix is announced, "False" otherwise"""
        return self._api.data["announced"]

    @property
    def asns(self):
        """A list of ("asn"/"holder") objects representing the originating ASNs. For multi-origin prefixes it's more than one ASN."""
        asns = []
        Asns = namedtuple("ASNs", ["asn", "holder"])

        for data in self._api.data["asns"]:
            asn = int(data["asn"])
            holder = str(data["holder"])

            tuple_data = {"asn": asn, "holder": holder}
            asns.append(Asns(**tuple_data))

        return asns

    @property
    def holder(self):
        """Descriptive name for the AS if AS is given, "null" otherwise"""
        holders = []
        Holders = namedtuple("Holders", ["holder"])

        for data in self._api.data["asns"]:
            holder = str(data["holder"])

            tuple_data = {"holder": holder}
            holders.append(Holders(**tuple_data))

        return holders

    @property
    def resource(self):
        """Outputs the prefix that the query is based on"""
        return ipaddress.ip_network(self._api.data["resource"])

    @property
    def type(self):
        """For this data call always "prefix"."""
        return str(self._api.data["type"])

    @property
    def related_prefixes(self):
        """List of related prefixes"""
        return self._api.data["related_prefixes"]

    @property
    def actual_num_related(self):
        """Total number of (returned and truncated) related prefixes."""
        return int(self._api.data["actual_num_related"])

    @property
    def num_filtered_out(self):
        """
        Number of prefixes (exact or related) filtered by low-visibility filter. This can be
        controlled by the parameter "min_peers_seeing".
        """
        return int(self._api.data["num_filtered_out"])

    @property
    def is_less_specific(self):
        """True if the information in the response is for a larger block than the one requested."""
        return self._api.data["is_less_specific"]

    @property
    def query_time(self):
        """Defines the query time the result is based on."""
        return datetime.fromisoformat(self._api.data["query_time"])
