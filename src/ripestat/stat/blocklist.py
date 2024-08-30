"""Provides the Blocklist endpoint."""
import ipaddress
from collections import namedtuple
from datetime import datetime
from typing import Optional

from ripestat.validators import Validators


class Blocklist:
    """
    This data call returns blocklist related data for a queried resource.

    Reference: `<https://stat.ripe.net/docs/02.data-api/blocklist.html>`_
    ======================= ===========================================================
    Property                Description
    ======================= ===========================================================
    ``source``              Each different data source gets one entry, containing blocklist information for this source.
    ``prefix``              Holds the prefix of the entry in the blocklist data source.
    ``details``             If available this holds additional informations about the entry.
    ``timelines``           Holds time information for the periods the entry appeared in the blocklist data source.
    ``query_starttime``     Defines the starttime the query covers.
    ``query_endtime``       Defines the endtime the query covers.
    ``resource``            Defines the resource used for the query.
    ======================= ===========================================================
    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()
        blocklist = ripe.blocklist('193/23')
    """

    PATH = "/blocklist"
    VERSION = "1.0"

    def __init__(
        self,
        RIPEstat,
        resource,
        starttime: Optional[datetime] = None,
        endtime: Optional[datetime] = None,
    ):
        """
        Initialize and request the blocklist related data for a queried resource.

        :param resource: Defines the resource that the query is performed for. (prefix
            or IP range)
        :param starttime: The start time for the query. (default earliest time there
            is Blocklist data available)
        :param endtime: The start time for the query. (default if not set it falls
            back to now)

        .. code-block:: python
            blocklist = ripe.blocklist("193/23", starttime="2016-08-31T00:00")
        """

        params = {
            "preferred_version": Blocklist.VERSION,
            "resource": str(resource),
        }

        if starttime:
            if Validators._validate_datetime(starttime):
                if not isinstance(starttime, datetime):
                    params["starttime"] = starttime
                else:
                    params["starttime"] = starttime.isoformat()
            else:
                raise ValueError("starttime expected to be datetime")
        if endtime:
            if Validators._validate_datetime(endtime):
                if not isinstance(endtime, datetime):
                    params["endtime"] = endtime
                else:
                    params["endtime"] = endtime.isoformat()
            else:
                raise ValueError("endtime expected to be datetime")

        self._api = RIPEstat._get(Blocklist.PATH, params)

    def __repr__(self):
        """Return the resource (prefix or IP range) and data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource (prefix or IP range) as string representation of the object."""
        return str(self.resource)

    # TODO: add __getitem__, __iter__ and __len__

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def sources(self):
        """
        A list of all blocklist information for this source.

        Returns a **list** of `Sources` named tuples with the following
        properties:

        =============   ========================================================
        Property        Description
        =============   ========================================================
        ``prefix``      Prefix of the entry **IPv4Network** or **IPv6Network**
        ``details``     Additional informations about the entry.
        ``timelines``   **List** of Timeline named tuples with properties
                        ``starttime`` and ``endtime``
        =============   ========================================================

        """
        sources = []
        Sources = namedtuple("Sources", ["prefix", "details", "timelines"])
        Timeline = namedtuple("Timeline", ["starttime", "endtime"])

        for source in self._api.data["sources"]["uceprotect-level1"]:
            prefix = ipaddress.ip_network(source["prefix"], strict=False)
            details = source["details"]
            timelines = []

            for timeline in source["timelines"]:
                starttime = datetime.fromisoformat(timeline["starttime"])
                endtime = datetime.fromisoformat(timeline["endtime"])

                timelines.append(Timeline(starttime=starttime, endtime=endtime))

            tuple_data = {"prefix": prefix, "details": details, "timelines": timelines}
            sources.append(Sources(**tuple_data))

        return sources

    @property
    def prefix(self):
        """A list of all prefix of the entry in the blocklist data source."""
        prefixes = []

        for source in self._api.data["sources"]["uceprotect-level1"]:
            prefix = ipaddress.ip_network(source["prefix"], strict=False)

            prefixes.append(prefix)

        return prefixes

    @property
    def details(self):
        """A list of all additional informations about the entry."""
        details = []

        for source in self._api.data["sources"]["uceprotect-level1"]:
            detail = source["details"]
            details.append(detail)

        return details

    @property
    def timelines(self):
        """
        A list of all time information for the periods the entry appeared
        in the blocklist data source.
        """
        timelines = []
        Timeline = namedtuple("Timeline", ["starttime", "endtime"])

        for source in self._api.data["sources"]["uceprotect-level1"]:
            timeline = []

            for data in source["timelines"]:
                starttime = datetime.fromisoformat(data["starttime"])
                endtime = datetime.fromisoformat(data["endtime"])

                timeline.append(Timeline(starttime=starttime, endtime=endtime))

            timelines.append(timeline)

        return timelines

    @property
    def query_endtime(self):
        """The **datetime** at which the query ended."""
        return datetime.fromisoformat(self._api.data["query_endtime"])

    @property
    def query_starttime(self):
        """The **datetime** at which the query started."""
        return datetime.fromisoformat(self._api.data["query_starttime"])

    @property
    def resource(self):
        """The resource used for the query."""
        try:
            return ipaddress.ip_network(self._api.data["resource"])
        except ValueError:
            return self._api.data["resource"]
