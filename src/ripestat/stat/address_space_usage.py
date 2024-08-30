"""Provides the Address Space Usage Status endpoint."""
from collections import namedtuple
from datetime import datetime
from ipaddress import IPv4Network


class AddressSpaceUsage:
    """
    This data call shows the usage of a prefix or IP range according to the objects
    currently present in the RIPE database. The data returned lists the assignments
    and allocations covered by the queried resource as well statistics on the total
    numbers of IPs in the different categories.

    Reference: `<https://stat.ripe.net/docs/02.data-api/address-space-usage.html>`_
    ======================= ===========================================================
    Property                Description
    ======================= ===========================================================
    ``assignments``         list of assignments from the allocations related to the queried resource.
    ``allocations``         list of allocations related to the queried resource.
    ``ip_stats``            overview of the distribution of statuses of the covered address space.
    ``resource``            Holds the resource the query was based on.
    ``query_time``          Holds the time the query was based on.
    ======================= ===========================================================
    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()

        # Lookup by IPv4 or IPv6 Address
        address_spaces = ripe.address_space_usage('193.0.0.0')
        from ipaddress import IPv4Address
        address_spaces = ripe.address_space_usage(IPv4Address('193.0.0.0'))
        # Lookup by IPv4 or IPv6 Network (prefix)
        from ipaddress import IPv4Network
        address_spaces = ripe.address_space_usage(IPv4Network('193.0.0.0/23'))

        # See each property below for additional details on each of the returned
        # properties listed in the table above.
        address_spaces.resource
        # IPv4Network('193.0.0.0/23')
        address_spaces.query_time
        # datetime.datetime(2021, 4, 14, 12, 54, 37)
    """

    PATH = "/address-space-usage"
    VERSION = "0.4"

    def __init__(
        self,
        RIPEstat,
        resource,
        all_level_more_specifics: bool = True,
    ):
        """
        Initialize and request the Address Space Usage.

        :param resource: States the prefix or IP range the address space usage should be returned for
        :param all_level_more_specifics: This parameter allows to control that
            all levels (True) or only the first level (False) of more-specific
            resources are returned. This can be helpful if large blocks of IP
            space are looked up and the number of returned resources is too big. (default True)

        .. code-block:: python
            address_spaces = ripe.address_space_usage('193/32')
        """

        params = {"preferred_version": AddressSpaceUsage.VERSION}

        params["resource"] = str(resource)
        if all_level_more_specifics:
            if isinstance(all_level_more_specifics, bool):
                params["all_level_more_specifics"] = str(all_level_more_specifics)
            else:
                raise ValueError("all_level_more_specifics expected to be bool")
        self._api = RIPEstat._get(AddressSpaceUsage.PATH, params)

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
    def query_time(self):
        """Holds the time the query was based on"""
        return datetime.fromisoformat(self._api.data["query_time"])

    @property
    def resource(self):
        """Holds the time the query was based on"""
        return IPv4Network(self._api.data["resource"])

    @property
    def assignments(self):
        """A list of assignments from the allocations related to the queried resource."""
        assignments = []
        AssignmentData = namedtuple(
            "assignments", ["address_range", "asn_name", "status", "parent_allocation"]
        )

        for assignment in self._api.data["assignments"]:
            address_range = assignment["address_range"]
            asn_name = assignment["asn_name"]
            status = assignment["status"]
            parent_allocation = assignment["parent_allocation"]

            assignment_data = {
                "address_range": address_range,
                "asn_name": asn_name,
                "status": status,
                "parent_allocation": parent_allocation,
            }
            assignments.append(AssignmentData(**assignment_data))

        return assignments

    @property
    def allocations(self):
        """A list of allocations related to the queried resource."""
        allications = []
        AllocationData = namedtuple(
            "allocations", ["allocation", "asn_name", "status", "assignments"]
        )

        for alloc in self._api.data["allocations"]:
            allocation = alloc["allocation"]
            asn_name = alloc["asn_name"]
            status = alloc["status"]
            assignments = alloc["assignments"]

            allocation_data = {
                "allocation": allocation,
                "asn_name": asn_name,
                "status": status,
                "assignments": assignments,
            }
            allications.append(AllocationData(**allocation_data))

        return allications

    @property
    def ip_stats(self):
        """An overview of the distribution of statuses of the covered address space."""
        ip_stats = []
        IpStatsData = namedtuple("ip_stats", ["status", "ips"])

        for ipstat in self._api.data["ip_stats"]:
            status = ipstat["status"]
            ips = ipstat["ips"]

            ip_data = {"status": status, "ips": ips}
            ip_stats.append(IpStatsData(**ip_data))

        return ip_stats
