from unittest.mock import patch

import easyinstaller.core.distro_detector as dd


def _reset_caches():
    dd.get_distro_id.cache_clear()
    dd.get_native_manager_type.cache_clear()


def test_get_native_manager_type_returns_expected_manager():
    _reset_caches()
    with patch(
        'easyinstaller.core.distro_detector.platform.freedesktop_os_release',
        return_value={'ID': 'Ubuntu'},
    ) as release_mock:
        assert dd.get_native_manager_type() == 'apt'
        # Second call should hit the cache and avoid re-invoking platform.
        assert dd.get_native_manager_type() == 'apt'
        assert release_mock.call_count == 1


def test_get_distro_id_handles_unknown_release():
    _reset_caches()
    with patch(
        'easyinstaller.core.distro_detector.platform.freedesktop_os_release',
        side_effect=OSError,
    ):
        assert dd.get_distro_id() == 'unknown'
        assert dd.get_native_manager_type() == 'unknown'


def test_get_distro_id_normalizes_to_lowercase():
    _reset_caches()
    with patch(
        'easyinstaller.core.distro_detector.platform.freedesktop_os_release',
        return_value={'ID': 'ARCH'},
    ):
        assert dd.get_distro_id() == 'arch'
