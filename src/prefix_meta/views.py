import csv
import ipaddress

from django.http import HttpResponse
from fullctl.django.decorators import load_instance, require_auth

from prefix_meta.models import Data


@require_auth()
@load_instance()
def export_locations(request, instance, ip, masklen, **kwargs):
    """
    CSV export of location data for a given prefix
    """

    try:
        prefix = ipaddress.ip_network(f"{ip}/{masklen}")
    except Exception:
        return HttpResponse(status=400)

    if not request.perms.check("meta.prefix.location.{org.permission_id}", "r"):
        return HttpResponse(status=403)

    qset = Data.objects.filter(prefix__net_contained_or_equal=prefix).order_by("prefix")

    file_id = str(prefix).replace("/", "_").replace(".", "-")

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="location-{file_id}.csv"'
        },
    )

    writer = csv.writer(response)

    headers = [
        "prefix",
        "country_code",
        "city_name",
        "region_name",
        "latitude",
        "longitude",
        "isp",
    ]

    lines = []

    locations = [location for location in qset]

    for loc in locations:
        data = loc.data.get("ip2location", {})
        for k in data.keys():
            if k not in headers:
                headers.append(k)

    for loc in locations:
        data = loc.data.get("ip2location", {})
        line = [f"{loc.prefix}"]
        for header in headers:
            if header in ["prefix"]:
                continue
            line.append(data.get(header))
        lines.append(line)

    writer.writerow(headers)

    for line in lines:
        writer.writerow(line)

    return response
