"""Provides the BGP updates endpoint."""
from collections import namedtuple
from datetime import datetime
from typing import Optional

from ripestat.validators import Validators


class BGPUpdates:
    """
    This data call returns the BGP updates observed for a resource over a certain period of time.

    Reference: `<https://stat.ripe.net/docs/02.data-api/bgp-updates.html>`_
    ======================= ===========================================================
    Property                Description
    ======================= ===========================================================
    ``updates``             List of observed BGP updates, in chronological order of occurrence.
    ``nr_updates``          The number of BGP updates observed in this time period.
    ``query_starttime``     Defines the start of the time interval covered in the query.
    ``query_endtime``       Defines the end of the time interval covered in the query.
    ``resource``            Defines the resource used in the query.
    ======================= ===========================================================
    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()
        updates = ripe.bgp_updates(140.78/16, starttime=2023-02-01T08:00, endtime=2023-02-02T11:00)
    """

    PATH = "/bgp-updates"
    VERSION = "1.1"

    def __init__(
        self,
        RIPEstat,
        resource,
        starttime: Optional[datetime] = None,
        endtime: Optional[datetime] = None,
        rrcs=None,
        unix_timestamps: bool = False,
    ):
        """
        Initialize and request the BGP updates.

        :param resource: Defines the resource that the query is performed for. (Prefix,
            IP address, AS or a list of valid comma-separated resources)
        :param starttime: The start time for the query. (default (endtime - 48h))
        :param endtime: The start time for the query. (default latest time there is
            BGP data available)
        :param rrcs: The list of Route Collectors (RRCs) to get the results from.
            (default behaviour: all RRCs)
        :param unix_timestamps: If TRUE, will format the timestamps in the result as
            Unix timestamp. (default False)

        .. code-block:: python
            bgp_updates = ripe.bgp_updates('140.78/16')
        """

        params = {
            "preferred_version": BGPUpdates.VERSION,
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
        if rrcs:
            if isinstance(rrcs, list):
                params["rrcs"] = ",".join(str(e) for e in rrcs)
            elif isinstance(rrcs, int):
                params["rrcs"] = str(rrcs)
            else:
                raise ValueError("rrcs value expected to be list of int")
        if unix_timestamps:
            if isinstance(unix_timestamps, bool):
                params["unix_timestamps"] = str(unix_timestamps)
            else:
                raise ValueError("unix_timestamps expected to be bool")

        self._api = RIPEstat._get(BGPUpdates.PATH, params)

    def __repr__(self):
        """Return the resource (ASN, IP address, IP prefix or resource list) and data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource (ASN, IP address, IP prefix or resource list) as string representation of the object."""
        return str(self.resource)

    # TODO: add __getitem__, __iter__ and __len__

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def updates(self):
        """
        A list of observed BGP updates, in chronological order of occurrence.

        Returns a **list** of `Updates` named tuples with the following
        properties:

        =============   ========================================================
        Property        Description
        =============   ========================================================
        ``type``        Type of BGP update: "A"=Announcement, "W"=Withdrawal.
        ``timestamp``   Time (UTC) of the BGP update.
        ``attrs``       **List** of Attrs named tuples with properties
                        ``target_prefix``, ``path``, ``community``, ``source_id``
        ``seq``         Sequential integer ordering the received BGP events
        =============   ========================================================

        """
        updates = []
        Updates = namedtuple("Updates", ["type", "timestamp", "attrs", "seq"])
        Attrs = namedtuple("Attrs", ["target_prefix", "path", "community", "source_id"])

        for update in self._api.data["updates"]:
            type = str(update["type"])
            timestamp = datetime.fromisoformat(update["timestamp"])
            seq = update["seq"]
            target_prefix = update["attrs"]["target_prefix"]
            source_id = update["attrs"]["source_id"]
            attrs = []

            try:
                community = update["attrs"]["community"]
                path = update["attrs"]["path"]
            except KeyError:
                community = []
                path = []

            attrs.append(
                Attrs(
                    target_prefix=target_prefix,
                    path=path,
                    community=community,
                    source_id=source_id,
                )
            )
            tuple_data = {
                "type": type,
                "timestamp": timestamp,
                "attrs": attrs,
                "seq": seq,
            }
            updates.append(Updates(**tuple_data))

        return updates

    @property
    def nr_updates(self):
        """The number of BGP updates observed in this time period."""
        return self._api.data["nr_updates"]

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
        """Defines the resource used for the query"""
        return self._api.data["resource"]
