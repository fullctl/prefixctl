from django.urls import reverse

# import django_prefixctl.models.prefixctl as models


def test_prefixset_list(db, account_objects):
    prefixset = account_objects.prefixset
    client = account_objects.api_client
    org = account_objects.org

    url = reverse("prefixctl_api:prefix_set-list", args=(org.slug,))
    print(url)

    response = client.get(
        reverse("prefixctl_api:prefix_set-list", args=(org.slug,)), follow=True
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == prefixset.name
    assert data[0]["id"] == prefixset.id
    assert data[0]["status"] == prefixset.status
