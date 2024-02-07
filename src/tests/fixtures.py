import fullctl.django.testutil as testutil
import pytest
from django.test import Client

# lazy init for translations
_ = lambda s: s  # noqa: E731


class AccountObjects(testutil.AccountObjects):
    @property
    def prefixctl_instance(self):
        from django_prefixctl.models import Instance

        if not hasattr(self, "_prefixctl_instance"):
            self._prefixctl_instance = Instance.objects.create(org=self.org)

        return self._prefixctl_instance

    @property
    def prefixset(self):
        from django_prefixctl.models import PrefixSet

        if hasattr(self, "_prefixset"):
            return self._prefixset

        self._prefixset = PrefixSet.objects.create(
            instance=self.prefixctl_instance,
            name="Test Prefixes",
        )

        return self._prefixset


def make_account_objects(handle="test"):
    return AccountObjects(handle)


@pytest.fixture
def client_anon():
    return Client()


@pytest.fixture
def account_objects():
    return make_account_objects()


@pytest.fixture
def account_objects_b():
    return make_account_objects("test_b")
