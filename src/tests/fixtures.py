import fullctl.django.testutil as testutil
from fullctl.django.models.concrete.tasks import TaskSchedule
import pytest
from django.test import Client
from django.utils import timezone

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
            description="Test Prefixes",
        )

        return self._prefixset

    @property
    def prefix(self):
        from django_prefixctl.models import Prefix

        if hasattr(self, "_prefix"):
            return self._prefix

        self._prefix = Prefix.objects.create(
            prefix_set=self.prefixset, prefix="192.168.0.0/24"
        )

        return self._prefix

    @property
    def asn_set(self):
        from django_prefixctl.models import ASNSet

        if hasattr(self, "_asn_set"):
            return self._asn_set

        self._asn_set = ASNSet.objects.create(
            instance=self.prefixctl_instance, name="ASN SET", description="Test ASN Set"
        )

        return self._asn_set

    @property
    def asn(self):
        from django_prefixctl.models import ASN

        if hasattr(self, "_asn"):
            return self._asn

        self._asn = ASN.objects.create(asn="1", asn_set=self.asn_set)

        return self._asn

    @property
    def asn_monitor(self):
        from django_prefixctl.models import ASNMonitor

        if hasattr(self, "_asn_monitor"):
            return self._asn_monitor

        self._asn_monitor = ASNMonitor.objects.create(
            instance=self.prefixctl_instance,
            asn_set=self.asn_set,
            new_prefix_detection=True,
        )

        return self._asn_monitor

    @property
    def prefix_monitor(self):
        from django_prefixctl.models import PrefixMonitor

        if hasattr(self, "_prefix_monitor"):
            return self._prefix_monitor

        self._prefix_monitor = PrefixMonitor.objects.create(
            instance=self.prefixctl_instance,
            prefix_set=self.prefixset,
            asn_set_origin=self.asn_set,
            asn_set_upstream=self.asn_set,
            alert_specifics=True,
            alert_dampening=True,
            roa_validation=True,
            task_schedule=TaskSchedule.objects.create(
                org=self.org,
                task_config={},
                description="test",
                repeat=True,
                interval=3600,
                schedule=timezone.now(),
            ),
        )

        return self._prefix_monitor

    @property
    def prefixset_irr_importer(self):
        from django_prefixctl.models import PrefixSetIRRImporter

        if hasattr(self, "_prefixset_irr_importer"):
            return self._prefixset_irr_importer

        self._prefixset_irr_importer = PrefixSetIRRImporter.objects.create(
            instance=self.prefixctl_instance, prefix_set=self.prefixset
        )

        return self._prefixset_irr_importer

    @property
    def alert_group(self):
        from django_prefixctl.models import AlertGroup

        if hasattr(self, "_alert_group"):
            return self._alert_group

        self._alert_group = AlertGroup.objects.create(
            name="Test Alert Group", instance=self.prefixctl_instance
        )

        return self._alert_group

    @property
    def alert_recipient(self):
        from django_prefixctl.models import AlertRecipient

        if hasattr(self, "_alert_recipient"):
            return self._alert_recipient

        self._alert_recipient = AlertRecipient.objects.create(
            alertgrp=self.alert_group, typ="email", recipient="test@gmail.com"
        )

        return self._alert_recipient

    @property
    def alert_log(self):
        from django_prefixctl.models import AlertLog

        if hasattr(self, "_alert_log"):
            return self._alert_log

        self._alert_log = AlertLog.objects.create(
            alertgrp=self.alert_group, subject="Test subject", message="Test message"
        )

        return self._alert_log

    @property
    def alert_log_recipient(self):
        from django_prefixctl.models import AlertLogRecipient

        if hasattr(self, "_alert_log_recipient"):
            return self._alert_log_recipient

        self._alert_log_recipient = AlertLogRecipient.objects.create(
            alertlog=self.alert_log, typ="email", recipient="test@gmail.com"
        )

        return self._alert_log_recipient


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
