import json
import pytest
from django.urls import reverse

import django_prefixctl.models.prefixctl as models


def test_prefixset_list(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(
        reverse("prefixctl_api:prefix_set-list", args=(org.slug,)), follow=True
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == prefixset.name
    assert data[0]["id"] == prefixset.id
    assert data[0]["status"] == prefixset.status


def test_prefixset_retreive(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    # Fetch one specific prefixset
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == prefixset.name
    assert data[0]["id"] == prefixset.id
    assert data[0]["status"] == prefixset.status


def test_retreive_non_existent_prefixset(db, account_objects):
    client = account_objects.api_client
    org = account_objects.org

    url = reverse(
        "prefixctl_api:prefix_set-detail", kwargs={"org_tag": org.slug, "pk": 40}
    )
    response = client.get(url)

    assert response.status_code == 404


def test_update_prefixset_name(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    # Update prefix set field name
    request_data = {"name": "New Prefix Set 6"}
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == request_data["name"]


def test_update_prefixset_description(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    # Update prefix set field description
    request_data = {
        "name": prefixset.name,
        "description": "New Prefix Set 6, version 9",
    }
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == prefixset.name
    assert data[0]["description"] == request_data["description"]


def test_update_prefixset_irr_import(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    assert prefixset.irr_import is False

    # update prefixset field irr_import
    request_data = {"name": prefixset.name, "irr_import": True, "irr_as_set": "aaaaaa"}
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["irr_import"]

    prefixset.refresh_from_db()
    assert prefixset.irr_import


def test_update_prefixset_ux_keep_list_open(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    assert prefixset.ux_keep_list_open is False

    # update prefixset field ux_keep_list_open
    request_data = {
        "name": prefixset.name,
        "ux_keep_list_open": True,
    }
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["ux_keep_list_open"]

    prefixset.refresh_from_db()
    assert prefixset.ux_keep_list_open


def test_create_prefixset(db, account_objects):
    client = account_objects.api_client
    org = account_objects.org

    # Create a prefixset
    data = {
        "name": "Test Prefixe 3",
        "description": None,
        "prefixes": [],
        "monitors": [],
        "irr_import": False,
        "irr_as_set": None,
        "irr_sources": None,
        "irr_import_status": "disabled",
        "num_monitors": 0,
        "num_prefixes": 0,
        "ux_keep_list_open": False,
        "grainy": "prefix.1.2",
    }

    url = reverse("prefixctl_api:prefix_set-list", args=(org.slug,))
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Test Prefixe 3"
    assert models.PrefixSet.objects.filter(id=data[0]["id"]).exists()


def test_delete_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    # prefix_monitor = account_objects.prefix_monitor
    client = account_objects.api_client
    org = account_objects.org

    # assert prefixset.prefix_monitor_set.all()[0].task_schedule

    # Delete a prefixset
    url = reverse(
        "prefixctl_api:prefix_set-detail",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )

    response = client.delete(url)

    assert response.status_code == 200
    assert models.PrefixSet.objects.filter(id=prefixset.id).exists() is False
    # assert prefixset.prefix_monitor_set.all().count() == 0
    # assert (
    #    models.TaskSchedule.objects.filter(id=prefix_monitor.task_schedule.id).exists()
    #    is False
    # )


@pytest.mark.skip(
    reason="No prefixctl monitor classes to test with (prefix monitor was moved to its own package)"
)
def test_add_monitor_to_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org
    asn_set = account_objects.asn_set

    # Add a monitor to a prefixset
    data = {
        "prefix_set": prefixset.id,
        "asn_set_origin": asn_set.id,
        "asn_set_upstream": asn_set.id,
        "asn_path": "string",
        "alert_specifics": True,
        "alert_dampening": True,
        "roa_validation": True,
        "monitor_type": "prefix_monitor",
    }

    url = reverse(
        "prefixctl_api:prefix_set-add-monitor",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.post(url, json.dumps(data), content_type="application/json")
    data = response.json()["data"]
    assert response.status_code == 201
    assert data[0]["instance"] == prefixset.instance.id
    assert data[0]["prefix_set"] == prefixset.id
    assert data[0]["asn_set_origin"] == asn_set.id
    assert data[0]["asn_set_origin_name"] == asn_set.name
    assert data[0]["asn_set_upstream"] == asn_set.id
    assert data[0]["asn_set_upstream_name"] == asn_set.name
    assert data[0]["status"] == "ok"


@pytest.mark.skip(
    reason="No prefixctl monitor classes to test with (prefix monitor was moved to its own package)"
)
def test_list_monitors_for_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org
    asn_set = account_objects.asn_set

    assert prefixset.prefix_monitor_set.all().count() == 0

    # Add a monitor
    data = {
        "prefix_set": prefixset.id,
        "asn_set_origin": asn_set.id,
        "asn_set_upstream": asn_set.id,
        "asn_path": "string",
        "alert_specifics": True,
        "alert_dampening": True,
        "roa_validation": True,
        "monitor_type": "prefix_monitor",
    }

    add_monitor_url = reverse(
        "prefixctl_api:prefix_set-add-monitor",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )

    client.post(add_monitor_url, json.dumps(data), content_type="application/json")

    assert prefixset.prefix_monitor_set.all().count() == 1

    # List all monitors
    response = client.get(
        reverse(
            "prefixctl_api:prefix_set-monitors",
            kwargs={"org_tag": org.slug, "pk": prefixset.id},
        )
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["instance"] == prefixset.instance.id
    assert data[0]["prefix_set"] == prefixset.id
    assert data[0]["asn_set_origin"] == asn_set.id
    assert data[0]["asn_set_origin_name"] == asn_set.name
    assert data[0]["asn_set_upstream"] == asn_set.id
    assert data[0]["asn_set_upstream_name"] == asn_set.name
    assert data[0]["status"] == "ok"


@pytest.mark.skip(
    reason="No prefixctl monitor classes to test with (prefix monitor was moved to its own package)"
)
def test_delete_monitor_for_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org
    asn_set = account_objects.asn_set

    assert prefixset.prefix_monitor_set.all().count() == 0

    # Add a monitor
    data = {
        "prefix_set": prefixset.id,
        "asn_set_origin": asn_set.id,
        "asn_set_upstream": asn_set.id,
        "asn_path": "string",
        "alert_specifics": True,
        "alert_dampening": True,
        "roa_validation": True,
        "monitor_type": "prefix_monitor",
    }

    add_monitor_url = reverse(
        "prefixctl_api:prefix_set-add-monitor",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )

    client.post(add_monitor_url, json.dumps(data), content_type="application/json")

    assert prefixset.prefix_monitor_set.all().count() == 1

    # Delete the monitor
    data = {
        "monitor_type": "prefix_monitor",
        "id": prefixset.prefix_monitor_set.all()[0].id,
    }
    response = client.delete(
        reverse(
            "prefixctl_api:prefix_set-delete-monitor",
            kwargs={"org_tag": org.slug, "pk": prefixset.id},
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert prefixset.prefix_monitor_set.all().count() == 0


def test_list_prefixset_prefixes(db, account_objects):
    prefixset = account_objects.prefixset
    prefix = account_objects.prefix
    client = account_objects.api_client
    org = account_objects.org

    # List all prefixset prefixes
    response = client.get(
        reverse(
            "prefixctl_api:prefix_set-prefixes",
            kwargs={"org_tag": org.slug, "pk": prefixset.id},
        )
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["prefix_set"] == prefixset.id
    assert data[0]["prefix"] == prefix.prefix
    assert data[0]["status"] == "ok"


def test_add_prefix_to_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    assert prefixset.prefix_set.all().count() == 0

    # Add prefix to prefixset
    data = {
        "prefix_set": prefixset.id,
        "prefix": "172.16.0.0/16",
        "mask_length_range": "exact",
    }

    url = reverse(
        "prefixctl_api:prefix_set-add-prefix",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.post(url, json.dumps(data), content_type="application/json")
    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["prefix_set"] == prefixset.id
    assert data[0]["prefix"] == "172.16.0.0/16"
    assert data[0]["status"] == "ok"
    assert prefixset.prefix_set.all().count() == 1


def test_add_prefixes_to_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    assert prefixset.prefix_set.all().count() == 0

    # Add prefixes to prefixset
    data = {
        "prefix_set": prefixset.id,
        "prefixes": ["172.16.0.0/16", "198.51.100.0/24"],
    }

    url = reverse(
        "prefixctl_api:prefix_set-add-prefixes",
        kwargs={"org_tag": org.slug, "pk": prefixset.id},
    )
    response = client.post(url, json.dumps(data), content_type="application/json")

    data = response.json()
    assert response.status_code == 200
    assert prefixset.prefix_set.all().count() == 2


def test_delete_prefix_from_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    prefix = account_objects.prefix
    client = account_objects.api_client
    org = account_objects.org

    # Delete the prefix
    data = {"id": prefix.id}
    response = client.delete(
        reverse(
            "prefixctl_api:prefix_set-delete-prefix",
            kwargs={"org_tag": org.slug, "pk": prefixset.id},
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert prefixset.prefix_set.all().count() == 0

def test_delete_prefixes_after_x_days(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    assert prefixset.all().count() == 1

    data = {"days": 0}
    response = client.post(
        reverse(
            "prefixctl_api:prefix_set-delete-prefixes",
            kwargs={"org_tag": org.slug, "pk": prefixset.id},
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert prefixset.all().count() == 0


def test_asnset_list(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    # List all asn_sets
    response = client.get(
        reverse("prefixctl_api:asn_set-list", args=(org.slug,)), follow=True
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == asn_set.name
    assert data[0]["id"] == asn_set.id


def test_create_asn_set(db, account_objects):
    client = account_objects.api_client
    org = account_objects.org

    # Create asn_net
    request_data = {
        "name": "ASN SET Test",
        "description": "ASN Set description",
    }

    url = reverse("prefixctl_api:asn_set-list", args=(org.slug,))
    response = client.post(
        url, json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == request_data["name"]
    assert data[0]["description"] == request_data["description"]
    assert models.ASNSet.objects.filter(id=data[0]["id"]).exists()


def test_update_asn_set_name(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    # Update asn_set name
    url = reverse(
        "prefixctl_api:asn_set-detail", kwargs={"org_tag": org.slug, "pk": asn_set.id}
    )
    request_data = {"name": "New ASN SET"}
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == request_data["name"]
    assert (
        models.ASNSet.objects.filter(id=data[0]["id"])[0].name == request_data["name"]
    )


def test_update_asn_set_description(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    # Update asn_set description
    url = reverse(
        "prefixctl_api:asn_set-detail", kwargs={"org_tag": org.slug, "pk": asn_set.id}
    )
    request_data = {"name": asn_set.name, "description": "New ASN description"}
    response = client.put(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == asn_set.name
    assert data[0]["description"] == request_data["description"]
    assert (
        models.ASNSet.objects.filter(id=data[0]["id"])[0].description
        == request_data["description"]
    )


def test_delete_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    # Delete asn_set
    url = reverse(
        "prefixctl_api:asn_set-detail", kwargs={"org_tag": org.slug, "pk": asn_set.id}
    )
    request_data = {"name": asn_set.name}
    response = client.delete(
        url,
        json.dumps(request_data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert models.ASNSet.objects.all().count() == 0


def test_list_all_asns_in_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    asn = account_objects.asn
    client = account_objects.api_client
    org = account_objects.org

    # List all asns in asn_set
    response = client.get(
        reverse(
            "prefixctl_api:asn_set-asns", kwargs={"org_tag": org.slug, "pk": asn_set.id}
        )
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["asn_set"] == asn_set.id
    assert data[0]["id"] == asn.id
    assert data[0]["status"] == "ok"


def test_add_asn_to_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    assert asn_set.asn_set.all().count() == 0

    # Add asn to asn_set
    request_data = {"asn_set": asn_set.id, "asn": 2147483647}

    url = reverse(
        "prefixctl_api:asn_set-add-asn", kwargs={"org_tag": org.slug, "pk": asn_set.id}
    )
    response = client.post(
        url, json.dumps(request_data), content_type="application/json"
    )
    data = response.json()["data"]
    assert response.status_code == 200
    assert data[0]["asn_set"] == asn_set.id
    assert data[0]["asn"] == request_data["asn"]
    assert data[0]["status"] == "ok"
    assert asn_set.asn_set.all().count() == 1


def test_delete_asn_from_asnset(db, account_objects):
    asn_set = account_objects.asn_set
    asn = account_objects.asn
    client = account_objects.api_client
    org = account_objects.org

    assert asn_set.asn_set.all().count() == 1

    # Delete the asn
    data = {"asn": asn.asn}
    response = client.delete(
        reverse(
            "prefixctl_api:asn_set-delete-asn",
            kwargs={"org_tag": org.slug, "pk": asn_set.id},
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert asn_set.asn_set.all().count() == 0


def test_list_all_monitors_associatd_with_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    asn_monitor = account_objects.asn_monitor
    client = account_objects.api_client
    org = account_objects.org

    response = client.get(
        reverse(
            "prefixctl_api:asn_set-monitors",
            kwargs={"org_tag": org.slug, "pk": asn_set.id},
        )
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["asn_set"] == asn_set.id
    assert data[0]["id"] == asn_monitor.id
    assert data[0]["asn_set_name"] == asn_set.name
    assert data[0]["monitor_type"] == "asn_monitor"
    assert data[0]["status"] == "ok"


def test_add_monitor_to_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    client = account_objects.api_client
    org = account_objects.org

    assert asn_set.asn_monitor_set.all().count() == 0

    # Add monitor to asn_set
    request_data = {
        "asn_set": asn_set.id,
        "new_prefix_detection": True,
        "monitor_type": "asn_monitor",
    }

    url = reverse(
        "prefixctl_api:asn_set-add-monitor",
        kwargs={"org_tag": org.slug, "pk": asn_set.id},
    )
    response = client.post(
        url, json.dumps(request_data), content_type="application/json"
    )
    data = response.json()["data"]
    assert response.status_code == 201
    assert data[0]["asn_set"] == asn_set.id
    assert data[0]["asn_set_name"] == asn_set.name
    assert data[0]["new_prefix_detection"] == request_data["new_prefix_detection"]
    assert data[0]["monitor_type"] == "asn_monitor"
    assert data[0]["status"] == "ok"


def test_delete_monitor_from_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    asn_monitor = account_objects.asn_monitor
    client = account_objects.api_client
    org = account_objects.org

    assert asn_set.asn_monitor_set.all().count() == 1

    # Delete the monitor associated to the asn_set
    data = {"id": asn_monitor.id, "monitor_type": "asn_monitor"}
    response = client.delete(
        reverse(
            "prefixctl_api:asn_set-delete-monitor",
            kwargs={"org_tag": org.slug, "pk": asn_set.id},
        ),
        json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert asn_set.asn_monitor_set.all().count() == 0
