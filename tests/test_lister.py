from unittest.mock import MagicMock, patch

import easyinstaller.core.lister as lister


def test_list_apt_packages_parses_expected_fields():
    stdout = "pkg1\t1.0\t1024\npkg2\t2.0\t2048\n"
    completed = MagicMock(stdout=stdout)
    with patch(
        'easyinstaller.core.lister.subprocess.run', return_value=completed
    ) as run_mock:
        packages = lister.list_apt_packages()

    run_mock.assert_called_once()
    assert packages == [
        {
            'name': 'pkg1',
            'version': '1.0',
            'size': '1.00 MB',
            'source': 'apt',
        },
        {
            'name': 'pkg2',
            'version': '2.0',
            'size': '2.00 MB',
            'source': 'apt',
        },
    ]


def test_list_apt_packages_returns_empty_on_error():
    with patch(
        'easyinstaller.core.lister.subprocess.run',
        side_effect=FileNotFoundError,
    ):
        assert lister.list_apt_packages() == []


def test_list_flatpak_packages_parses_tab_columns():
    stdout = (
        "App One\torg.example.One\t1.2.3\t200 MB\n"
        "App Two\torg.example.Two\tlatest\t150 MB\n"
    )
    completed = MagicMock(stdout=stdout)
    with patch(
        'easyinstaller.core.lister.subprocess.run', return_value=completed
    ):
        packages = lister.list_flatpak_packages()

    assert packages[0]['name'] == 'App One'
    assert packages[0]['id'] == 'org.example.One'
    assert packages[1]['size'] == '150 MB'


def test_list_snap_packages_skips_header_and_extracts_fields():
    stdout = (
        "Name Version Rev Tracking Publisher Notes\n"
        "snap1 1.0 1 latest dev classic\n"
        "snap2 2.0 2 latest dev -\n"
    )
    completed = MagicMock(stdout=stdout)
    with patch(
        'easyinstaller.core.lister.subprocess.run', return_value=completed
    ):
        packages = lister.list_snap_packages()

    assert packages == [
        {'name': 'snap1', 'version': '1.0', 'size': 'N/A', 'source': 'snap'},
        {'name': 'snap2', 'version': '2.0', 'size': 'N/A', 'source': 'snap'},
    ]


def test_get_installed_snap_packages_set_handles_missing_binary():
    with patch(
        'easyinstaller.core.lister.subprocess.run',
        side_effect=FileNotFoundError,
    ):
        assert lister.get_installed_snap_packages_set() == set()


def test_unified_lister_aggregates_requested_managers():
    with patch(
        'easyinstaller.core.lister.list_apt_packages',
        return_value=[{'source': 'apt'}],
    ) as apt_mock, patch(
        'easyinstaller.core.lister.list_snap_packages',
        return_value=[{'source': 'snap'}],
    ) as snap_mock, patch(
        'easyinstaller.core.lister.list_flatpak_packages',
        return_value=[{'source': 'flatpak'}],
    ) as flatpak_mock:
        results = lister.unified_lister(['apt', 'snap', 'unknown'])

    apt_mock.assert_called_once()
    snap_mock.assert_called_once()
    flatpak_mock.assert_not_called()
    assert {entry['source'] for entry in results} == {'apt', 'snap'}
