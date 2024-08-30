"""
prefix meta utility functions
"""

import ipaddress

__all__ = [
    "prefix_to_net_handle",
]


def prefix_to_net_handle(prefix):
    """
    Convert a prefix to a net handle in the format of "NET-XXX-XXX-XXX-XXX-XXX"
    """

    if isinstance(prefix, str):
        prefix = ipaddress.ip_network(prefix)

    return "NET-%s-1" % "-".join(prefix.network_address.exploded.split("."))
