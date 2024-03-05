from django.conf import settings


def test_asn_set(db, account_objects):
    asn_set = account_objects.asn_set
    instance = account_objects.prefixctl_instance

    assert asn_set.name == "ASN SET"
    assert asn_set.description == "Test ASN Set"
    assert asn_set.instance == instance


def test_asn(db, account_objects):
    asn = account_objects.asn
    asn_set = account_objects.asn_set

    assert asn.asn == "1"
    assert asn_set == asn_set


def test_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    instance = account_objects.prefixctl_instance

    assert prefixset.name == "Test Prefixes"
    assert prefixset.instance == instance
    assert prefixset.description == "Test Prefixes"
    assert prefixset.irr_import is False
    assert prefixset.irr_as_set is None
    assert prefixset.irr_sources is None
    assert prefixset.status == "ok"
    assert prefixset.prefix_set.all().count() == 0
    assert prefixset.org == account_objects.org
    assert prefixset.irr_import_status == "disabled"


def test_adding_prefix_to_prefixset(db, account_objects):
    prefixset = account_objects.prefixset

    assert prefixset.prefix_set.all().count() == 0

    created, updated = prefixset.add_or_update_prefix(
        prefix="192.168.0.0/24", mask_length_range="exact"
    )

    assert created is True
    assert updated is False
    assert prefixset.prefix_set.all().count() == 1


def test_updating_prefix_through_prefixset(db, account_objects):
    prefixset = account_objects.prefixset
    _ = account_objects.prefix

    created, updated = prefixset.add_or_update_prefix(
        prefix="192.168.0.0/24", mask_length_range="[24, 24]"
    )

    assert created is False
    assert updated is True


def test_prefixset_irr_importer(db, account_objects):
    prefixset_irr_importer = account_objects.prefixset_irr_importer
    prefixset = account_objects.prefixset
    instance = account_objects.prefixctl_instance

    assert prefixset_irr_importer.prefix_set == prefixset
    assert prefixset_irr_importer.instance == instance
    assert prefixset_irr_importer.schedule_interval == settings.IRR_IMPORT_FREQUENCY
    assert prefixset_irr_importer.schedule_task_config == {
        "tasks": [
            {
                "op": "task_irr_import",
                "param": {
                    "args": [prefixset.id],
                    "kwargs": {},
                },
            }
        ]
    }


def test_prefix(db, account_objects):
    prefix = account_objects.prefix
    prefixset = account_objects.prefixset

    assert prefix.prefix == "192.168.0.0/24"
    assert prefix.prefix_set == prefixset
    assert prefix.mask_length_range == "exact"


def test_asn_monitor(db, account_objects):
    asn_monitor = account_objects.asn_monitor
    asn_set = account_objects.asn_set
    instance = account_objects.prefixctl_instance

    assert asn_monitor.asn_set == asn_set
    assert asn_monitor.instance == instance
    assert asn_monitor.new_prefix_detection is True


def test_alert_group(db, account_objects):
    alert_group = account_objects.alert_group
    instance = account_objects.prefixctl_instance

    assert alert_group.instance == instance
    assert alert_group.name == "Test Alert Group"
    assert instance.alertgrp_set.all().count() == 1


def test_alert_recipient(db, account_objects):
    alert_recipient = account_objects.alert_recipient
    alert_group = account_objects.alert_group

    assert alert_recipient.alertgrp == alert_group
    assert alert_recipient.typ == "email"
    assert alert_recipient.recipient == "test@gmail.com"
    assert alert_group.alertrcp_set.all().count() == 1


def test_alert_log(db, account_objects):
    alert_log = account_objects.alert_log
    alert_group = account_objects.alert_group

    assert alert_log.alertgrp == alert_group
    assert alert_log.subject == "Test subject"
    assert alert_log.message == "Test message"
    assert alert_group.alertlog_set.all().count() == 1


def test_alert_log_recipient(db, account_objects):
    alert_log_recipient = account_objects.alert_log_recipient
    alert_log = account_objects.alert_log

    assert alert_log_recipient.alertlog == alert_log
    assert alert_log_recipient.typ == "email"
    assert alert_log_recipient.recipient == "test@gmail.com"
    assert alert_log.alert_log_recipient_set.all().count() == 1
