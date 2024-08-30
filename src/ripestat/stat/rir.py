"""Provides the Prefix RIR endpoint."""
from collections import namedtuple
from datetime import datetime
from typing import Optional

from ripestat.validators import Validators


class RIR:
    """
    This data call shows which RIR(s) allocated/assigned a resource. Depending on the level of detail
    ("lod" parameter) this can include additional information like registration status or country of
    registration. The data is based on RIR stats files, see ftp://ftp.ripe.net/pub/stats/.

    Reference: `<https://stat.ripe.net/docs/02.data-api/rir.html>`_

    .. code-block:: python

        import ripestat

        ripe = ripestat.RIPEstat()
        rir = ripe.rir("193.0.0.0/16")

    """

    PATH = "/rir"
    VERSION = "0.1"

    def __init__(
        self,
        RIPEstat,
        resource,
        starttime: Optional[datetime] = None,
        endtime: Optional[datetime] = None,
        lod: int = None,
    ):
        """
        Initialize and request the RIR(s).

        :param resource: Defines the resource to be queried. (IP resource / ASN)
        :param starttime: The start time for the query. (default latest time data is available for.)
        :param endtime: The start time for the query. (default latest time data is available for.)
        :param lod: Defines the level of detail in which the data is being returned. (Default is 1)
            Levels are:
            * 0 - Least detailed output
            * 1 - Default output
            * 2 - Most detailed output

        .. code-block:: python
            rir = ripe.rir("193.0.0.0/16")

        """
        params = {
            "preferred_version": RIR.VERSION,
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
        if lod:
            if isinstance(lod, int):
                params["lod"] = str(lod)
            else:
                raise ValueError("lod expected to be int")

        self._api = RIPEstat._get(RIR.PATH, params)

    def __repr__(self):
        """Return the resource IP resource / ASN and returned data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource IP resource / ASN representation of the object."""
        return str(self.resource)

    def __getitem__(self, index):
        """Get a specific index of the returned rirs."""
        return self.rirs[index]

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
        return self.rirs.__iter__()

    def __len__(self):
        """Get the number of rirs in RIR."""
        return len(self.rirs)

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
        return self._api.data["resource"]

    @property
    def latest(self):
        """Latest time data is available for."""
        return datetime.fromisoformat(self._api.data["latest"])

    @property
    def query_starttime(self):
        """The **datetime** at which the query started."""
        return datetime.fromisoformat(self._api.data["query_starttime"])

    @property
    def query_endtime(self):
        """The **datetime** at which the query ended."""
        return datetime.fromisoformat(self._api.data["query_endtime"])

    @property
    def lod(self):
        """
        Defines the level of detail in which the data is being returned.
        Levels are:
            * 0 - Least detailed output
            * 1 - Default output
            * 2 - Most detailed output
        """
        return int(self._api.data["lod"])

    @property
    def rirs(self):
        """A list of which RIR(s) allocated/assigned a resource."""
        rirs = []
        Rirs = namedtuple("RIRs", ["rir", "first_time", "last_time"])

        for data in self._api.data["rirs"]:
            rir = data["rir"]
            first_time = datetime.fromisoformat(data["first_time"])
            last_time = datetime.fromisoformat(data["last_time"])

            tuple_data = {"rir": rir, "first_time": first_time, "last_time": last_time}
            rirs.append(Rirs(**tuple_data))

        return rirs
