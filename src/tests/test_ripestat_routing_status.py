import os
import json
import datetime
import prefix_meta.sources.ripestat.routing_status as routing_status
from django.utils import timezone

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "prefix_meta")

def test_seen_in_routing_tables(db, account_objects):

    prefix = "216.176.40.0/22"

    # open data/prefix_meta/routing_status/meta.json

    with open(os.path.join(DATA_PATH, "routing_status", "meta.json")) as f:
        metadata = json.load(f)

    now = timezone.now()
    # zero milliseconds
    now = now.replace(microsecond=0)

    data = routing_status.RoutingStatusData(data=metadata, prefix=prefix, date=now)

    # test 1 - main target prefix is NOT currently visible, but more specifics are
    seen = data.seen_in_routing_tables(now)

    assert seen == [
        {
            "prefix": prefix,
            "seen": False,
            "more_specific": False,
            "last_seen": datetime.datetime(2023, 12, 14, 16, 0, tzinfo=datetime.timezone.utc),
        },
        {
            "prefix": "216.176.40.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.41.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.42.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.43.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
    ]

    # test 2 - main target prefix is currently visible, and more specifics are as well 

    metadata["last_seen"]["time"] = now.strftime("%Y-%m-%dT%H:%M:%S")
    data = routing_status.RoutingStatusData(data=metadata, prefix=prefix, date=now)
    seen = data.seen_in_routing_tables(now)

    assert seen == [
        {
            "prefix": prefix,
            "seen": True,
            "more_specific": False,
            "last_seen": now,
        },
        {
            "prefix": "216.176.40.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.41.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.42.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
        {
            "prefix": "216.176.43.0/24",
            "seen": True,
            "more_specific": True,
            "last_seen": now,
        },
    ]

    # test 3 - main target prefix is currently visible, but more specifics are not

    metadata["more_specifics"] = []
    data = routing_status.RoutingStatusData(data=metadata, prefix=prefix, date=now)
    seen = data.seen_in_routing_tables(now)

    assert seen == [
        {
            "prefix": prefix,
            "seen": True,
            "more_specific": False,
            "last_seen": now,
        },
    ]

    # test 4 - main target prefix is NOT currently visible, and more specifics are neither

    metadata["last_seen"] = {}
    data = routing_status.RoutingStatusData(data=metadata, prefix=prefix, date=now)
    seen = data.seen_in_routing_tables(now)

    assert seen == [
        {
            "prefix": prefix,
            "seen": False,
            "more_specific": False,
            "last_seen": None
        },
    ]