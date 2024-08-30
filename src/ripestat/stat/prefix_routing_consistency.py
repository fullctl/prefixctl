"""Provides the Prefix Routing Consistency endpoint."""
from datetime import datetime
from ipaddress import IPv4Network


class PrefixRoutingConsistency:
    """
    This data call compares the given routes (prefix originating from an ASN) between Routing
    Registries and actual routing behaviour as seen by the RIPE NCC route collectors

    Reference: `<https://stat.ripe.net/docs/02.data-api/prefix-routing-consistency.html>`_
    ======================= ===========================================================
    Property                Description
    ======================= ===========================================================
    ``in_bgp``              Boolean value is "True" if the route has been seen by RIS, "False" otherwise
    ``in_whois``            Boolean value is "True" if the route exists in whois, "False" otherwise
    ``origin``              AS number (integer) of the route
    ``asn_name``            The name of this AS's holder
    ``prefix``              Prefix (CIDR string) of the route (more or less specific to the input resource)
    ``irr_sources``         IRR source this route was found in e.g. "RADB", "RIPE", "LEVEL3"...
    ``query_time``          Holds the time the query was based on.
    ``resource``            Defines the resource used for the query
    ======================= ===========================================================
    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()

        # Lookup by IPv4 or IPv6 Network (prefix)
        from ipaddress import IPv4Network
        origin = ripe.prefix_routing_consistency(IPv4Network('193.0.20.0/24'))

        # See each property below for additional details on each of the returned
        # properties listed in the table above.
        origin.resource
        # IPv4Network('193.0.20.0/24')
        origin.query_time
        # datetime.datetime(2021, 4, 14, 12, 54, 37)
    """

    PATH = "/prefix-routing-consistency"
    VERSION = "1.1"

    def __init__(
        self,
        RIPEstat,
        resource,
    ):
        """
        Initialize and request origin ASN.

        :param resource: The prefix to query

        .. code-block:: python
            origin = ripe.prefix_routing_consistency('193/32')
        """

        params = {"preferred_version": PrefixRoutingConsistency.VERSION}

        params["resource"] = str(resource)

        self._api = RIPEstat._get(PrefixRoutingConsistency.PATH, params)

    def __repr__(self):
        """Return the resource (prefix or IP range) and data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource (prefix or IP range) as string representation of the object."""
        return str(self.resource)

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def in_bgp(self):
        """Boolean value is "True" if the route has been seen by RIS, "False" otherwise"""
        in_bgp = []
        for bgp in self._api.data["routes"]:
            data = bgp["in_bgp"]
            in_bgp.append(data)
        return in_bgp

    @property
    def in_whois(self):
        """Boolean value is "True" if the route exists in whois, "False" otherwise"""
        in_whois = []
        for who in self._api.data["routes"]:
            data = who["in_whois"]
            in_whois.append(data)
        return in_whois

    @property
    def origin(self):
        """AS number (integer) of the route"""
        origins = []
        for origin in self._api.data["routes"]:
            data = origin["origin"]
            origins.append(data)
        return origins

    @property
    def asn_name(self):
        """The name of this AS's holder"""
        asn_names = []
        for asn_name in self._api.data["routes"]:
            data = asn_name["asn_name"]
            asn_names.append(data)
        return asn_names

    @property
    def prefix(self):
        """Prefix (CIDR string) of the route (more or less specific to the input resource)"""
        prefixs = []
        for prefix in self._api.data["routes"]:
            data = prefix["prefix"]
            prefixs.append(data)
        return prefixs

    @property
    def irr_sources(self):
        """IRR source this route was found in e.g. "RADB", "RIPE", "LEVEL3"..."""
        irr_sources = []
        for irr_source in self._api.data["routes"]:
            data = irr_source["irr_sources"]
            irr_sources.append(data)
        return irr_sources

    @property
    def query_time(self):
        """Holds the time the query was based on"""
        return datetime.fromisoformat(self._api.data["query_time"])

    @property
    def resource(self):
        """Defines the resource used for the query"""
        return IPv4Network(self._api.data["resource"])
