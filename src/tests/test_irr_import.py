from django_prefixctl.irr import perform_irr_import


def test_import_prefixes_when_irr_import_is_disabled(db, account_objects):
    prefixset = account_objects.prefixset
    as_set = "AS-EXAMPLE"

    result = perform_irr_import(prefixset, as_set)

    assert result == {"error": "irr import disabled"}


def test_import_prefixes_when_irr_import_is_enabled(db, account_objects, mocker):
    prefixset = account_objects.prefixset
    prefixset.irr_import = True
    prefixset.save()
    as_set = "AS-EXAMPLE"

    assert prefixset.prefix_set.all().count() == 0

    # Mock subprocess.run()
    mock_run = mocker.patch("django_prefixctl.irr.subprocess.run")
    mock_run.return_value.stdout.decode.return_value = (
        '{"NN": [{"prefix": "192.0.2.0/24", "exact": true}]}'
    )
    # Set a return value for stderr to avoid raising an exception
    mock_run.return_value.stderr = b""

    result = perform_irr_import(prefixset, as_set)

    assert result == {
        "added": [("192.0.2.0/24", "exact")],
        "updated": [],
        "removed": [],
    }
    assert prefixset.prefix_set.all().count() == 1
    assert prefixset.prefix_set_irr_importer.require_task_schedule
    assert prefixset.prefix_set_irr_importer.task_schedule


def test_import_prefixes_to_be_updated(db, account_objects, mocker):
    prefixset = account_objects.prefixset
    _ = account_objects.prefix
    prefixset.irr_import = True
    prefixset.save()
    as_set = "AS-EXAMPLE"

    # Mock subprocess.run()
    mock_run = mocker.patch("django_prefixctl.irr.subprocess.run")
    mock_run.return_value.stdout.decode.return_value = (
        '{"NN": [{"prefix": "192.168.0.0/24", "exact": ""}]}'
    )
    # Set a return value for stderr to avoid raising an exception
    mock_run.return_value.stderr = b""

    result = perform_irr_import(prefixset, as_set)

    assert result == {
        "added": [],
        "updated": [("192.168.0.0/24", "")],
        "removed": [("192.168.0.0/24", "exact")],
    }
    assert prefixset.prefix_set_irr_importer.require_task_schedule
    assert prefixset.prefix_set_irr_importer.task_schedule


def test_import_prefixes_to_be_deleted(db, account_objects, mocker):
    prefixset = account_objects.prefixset
    _ = account_objects.prefix
    prefixset.irr_import = True
    prefixset.save()
    as_set = "AS-EXAMPLE"

    assert prefixset.prefix_set.all().count() == 1

    # Mock subprocess.run()
    mock_run = mocker.patch("django_prefixctl.irr.subprocess.run")
    mock_run.return_value.stdout.decode.return_value = (
        '{"NN": [{"prefix": "192.0.2.0/24", "exact": true}]}'
    )
    # Set a return value for stderr to avoid raising an exception
    mock_run.return_value.stderr = b""

    result = perform_irr_import(prefixset, as_set)

    assert prefixset.prefix_set.all().count() == 1

    assert result == {
        "added": [("192.0.2.0/24", "exact")],
        "updated": [],
        "removed": [("192.168.0.0/24", "exact")],
    }
    assert prefixset.prefix_set_irr_importer.require_task_schedule
    assert prefixset.prefix_set_irr_importer.task_schedule
