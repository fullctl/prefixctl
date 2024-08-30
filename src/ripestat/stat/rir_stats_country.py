"""Provides the Prefix RIR Stats Country endpoint."""
from collections import namedtuple
from datetime import datetime
from typing import Optional

from ripestat.validators import Validators


class RIRStatsCountry:
    """
    This data call returns geographical information for Internet resources based on
    RIR Statistics data.

    Reference: `<https://stat.ripe.net/docs/02.data-api/rir-stats-country.html>`_

    .. code-block:: python

        import ripestat

        ripe = ripestat.RIPEstat()
        rir = ripe.rir_stats_country("2001:67c:2e8::/48")

    """

    PATH = "/rir-stats-country"
    VERSION = "1.0"

    def __init__(
        self,
        RIPEstat,
        resource,
        query_time: Optional[datetime] = None,
    ):
        """
        Initialize and request the RIR Stats Country.

        :param resource: Defines the resource to be queried. (IP resource / ASN)
        :param query_time: Defines the times for the query, must be within the
            range of "earliest_time" and "latest_time". (default is time for which
            the lastest data is available)

        .. code-block:: python
            rir = ripe.rir_stats_country("2001:67c:2e8::/48")

        """
        params = {
            "preferred_version": RIRStatsCountry.VERSION,
            "resource": str(resource),
        }

        if query_time:
            if Validators._validate_datetime(query_time):
                if not isinstance(query_time, datetime):
                    params["query_time"] = query_time
                else:
                    params["query_time"] = query_time.isoformat()
            else:
                raise ValueError("starttime expected to be datetime")

        self._api = RIPEstat._get(RIRStatsCountry.PATH, params)

    def __repr__(self):
        """Return the resource IP resource / ASN and returned data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource IP resource / ASN representation of the object."""
        return str(self.resource)

    def __getitem__(self, index):
        """Get a specific index of the returned located_resources."""
        return self.located_resources[index]

    def __iter__(self):
        """
        Provide a way to iterate over rirs.

        .. code-block:: python

            import ripestat

            ripe = ripestat.RIPEstat()
            rir = ripe.rir("193.0.0.0/16")

            for data in rirs:
                print(data.rir, data.first_time, data.last_time)

        """
        return self.located_resources.__iter__()

    def __len__(self):
        """Get the number of located_resources that available from query result."""
        return len(self.located_resources)

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def resource(self):
        """
        Defines the resource to be queried. The result contains resources that are more
        or less specific to the queried resource.
        """
        return self._api.data["parameters"]["resource"]

    @property
    def located_resources(self):
        """A list all of located resource."""
        located_resources = []
        LocatedResources = namedtuple("LocatedResources", ["resource", "location"])

        for data in self._api.data["located_resources"]:
            resource = data["resource"]
            location = data["location"]

            tuple_data = {"resource": resource, "location": location}
            located_resources.append(LocatedResources(**tuple_data))

        return located_resources

    @property
    def result_time(self):
        """Contains the data of query time."""
        return datetime.fromisoformat(self._api.data["result_time"])

    @property
    def parameters(self):
        """Parameter that used for the query."""
        parameters = []
        Parameters = namedtuple("Parameters", ["resource", "query_time", "cache"])

        resource = self._api.data["parameters"]["resource"]
        query_time = datetime.fromisoformat(self._api.data["parameters"]["query_time"])
        cache = self._api.data["parameters"]["cache"]

        tuple_data = {"resource": resource, "query_time": query_time, "cache": cache}
        parameters.append(Parameters(**tuple_data))

        return parameters

    @property
    def earliest_time(self):
        """The **datetime** at which the earliest data is available."""
        return datetime.fromisoformat(self._api.data["earliest_time"])

    @property
    def latest_time(self):
        """The **datetime** at which the latest data is available."""
        return datetime.fromisoformat(self._api.data["latest_time"])
