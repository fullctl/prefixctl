"""Provide the RIPEstat class."""

from functools import partial
from typing import Optional, Type

from .api import get
from .stat.address_space_usage import AddressSpaceUsage
from .stat.announced_prefixes import AnnouncedPrefixes
from .stat.bgp_updates import BGPUpdates
from .stat.blocklist import Blocklist
from .stat.historical_whois import HistoricalWhois
from .stat.prefix_overview import PrefixOverview
from .stat.prefix_routing_consistency import PrefixRoutingConsistency
from .stat.rir import RIR
from .stat.rir_stats_country import RIRStatsCountry
from .stat.routing_status import RoutingStatus
from .stat.rpki_validation_status import RPKIValidationStatus


class RIPEstat:
    """
    The RIPEstat class provides a convenient way to access the RIPEstat public API.

    Instances of this class are the gateway to interacting with RIPE's stat API
    through RIPE Stat Data Parser. **If you have a `sourceapp` parameter from RIPE, see `__init__`
    documentation for details.**

    .. code-block:: python

        import ripestat

        ripe = ripestat.RIPEstat()

    """

    def __init__(
        self, data_overload_limit: Optional[str] = "", sourceapp: Optional[str] = ""
    ) -> None:
        """
        Initialize a RIPEstat instance.

        :param data_overload_limit: Override the soft-limit check (
            see `data_overload_limit()`)
        :param sourceapp: A unique identifier attached to API calls. This identifier
            helps RIPE assit you when you encounter any problems with the system. The
            identifier can be your project name or your company's. See
            `RIPEstat API Overview <https://stat.ripe.net/docs/data_api/#Overview>`_
            for details.
        """
        self.sourceapp = sourceapp
        self.data_overload_limit = data_overload_limit

        return

    @property
    def data_overload_limit(self) -> str:
        """
        The data overload prevention is to protect users, especially widgets, from
        getting more data than they can handle. For this reason some data calls already
        support a soft-limit check which returns a warning if the output looks to be
        more than usual.

        This prevention mechanism should only kick in if the request stems from a
        browser (the referrer header set), but in case it happens for a non-browser
        request, it can easily suppressed by the "data_overload_limit" parameter set
        to "ignore".
        """
        return self._data_overload_limit

    @data_overload_limit.setter
    def data_overload_limit(self, string):
        if string == "ignore" or string == "":
            self._data_overload_limit = string
        else:
            raise ValueError("data_overload_limit expected 'ignore' or blank string")

    def _get(self, path, params=None):
        """Retrieve the requested path with parameters as GET from the API."""
        params = {} if params is None else params

        if self.data_overload_limit:
            params["data_overload_limit"] = "ignore"
        if self.sourceapp:
            params["sourceapp"] = self.sourceapp

        return get(path, params)

    @property
    def address_space_usage(self) -> Type[AddressSpaceUsage]:
        """Lazy alias to :class:`.stat.AddressSpaceUsage`."""
        return partial(AddressSpaceUsage, self)

    @property
    def announced_prefixes(self) -> Type[AnnouncedPrefixes]:
        """Lazy alias to :class:`.stat.AnnouncedPrefixes`."""
        return partial(AnnouncedPrefixes, self)

    @property
    def prefix_routing_consistency(self) -> Type[PrefixRoutingConsistency]:
        """Lazy alias to :class:`.stat.PrefixRoutingConsistency`."""
        return partial(PrefixRoutingConsistency, self)

    @property
    def bgp_updates(self) -> Type[BGPUpdates]:
        """Lazy alias to :class:`.stat.BGPUpdates`."""
        return partial(BGPUpdates, self)

    @property
    def blocklist(self) -> Type[Blocklist]:
        """Lazy alias to :class:`.stat.Blocklist`."""
        return partial(Blocklist, self)

    @property
    def historical_whois(self) -> Type[HistoricalWhois]:
        """Lazy alias to :class:`.stat.HistoricalWhois`."""
        return partial(HistoricalWhois, self)

    @property
    def prefix_overview(self) -> Type[PrefixOverview]:
        """Lazy alias to :class:`.stat.PrefixOverview`."""
        return partial(PrefixOverview, self)

    @property
    def rir(self) -> Type[RIR]:
        """Lazy alias to :class:`.stat.RIR`."""
        return partial(RIR, self)

    @property
    def rir_stats_country(self) -> Type[RIRStatsCountry]:
        """Lazy alias to :class:`.stat.RIRStatsCountry`."""
        return partial(RIRStatsCountry, self)

    @property
    def rpki_validation_status(self) -> Type[RPKIValidationStatus]:
        """Lazy alias to :class:`.stat.RPKIValidationStatus`."""
        return partial(RPKIValidationStatus, self)

    @property
    def routing_status(self) -> Type[RoutingStatus]:
        """Lazy alias to :class:`.stat.RouteStatus`."""
        return partial(RoutingStatus, self)
