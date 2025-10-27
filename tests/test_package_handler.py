from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import easyinstaller.core.package_handler as ph


def test_build_cmd_apt_purge_uses_purge_flag():
    with patch(
        'easyinstaller.core.package_handler.get_native_manager_type',
        return_value='apt',
    ):
        cmd = ph._build_cmd('apt', 'remove', 'vim', purge=True)
    assert cmd == 'sudo -E apt-get purge -y vim'


def test_build_cmd_snap_install():
    cmd = ph._build_cmd('snap', 'install', 'code')
    assert cmd == 'sudo snap install code'


def test_build_cmd_unknown_manager_raises():
    with pytest.raises(ValueError):
        ph._build_cmd('brew', 'install', 'wget')


def test_build_cmd_unknown_native_manager_raises():
    with patch(
        'easyinstaller.core.package_handler.get_native_manager_type',
        return_value='unknown',
    ):
        with pytest.raises(ValueError):
            ph._build_cmd('apt', 'install', 'vim')


def test_install_with_manager_success(tmp_path):
    package_name = 'example-app'
    lister_states = iter(
        [
            {'base-package'},
            {'base-package', package_name},
        ]
    )

    def fake_lister():
        return set(next(lister_states))

    log_mock = MagicMock()
    with patch.dict(ph.MANAGER_TO_LISTER, {'snap': fake_lister}, clear=True):
        with patch.object(ph, 'config', {'log_dir': str(tmp_path)}):
            with patch(
                'easyinstaller.core.package_handler._ensure_manager_installed'
            ), patch(
                'easyinstaller.core.package_handler.run_cmd_smart',
                return_value=0,
            ) as run_mock, patch.object(
                ph.console, 'print'
            ) as console_mock, patch(
                'easyinstaller.core.package_handler.log_operation', log_mock
            ):
                ph.install_with_manager(package_name, 'snap')

    # Command invocation.
    run_mock.assert_called_once_with(
        f'sudo snap install {package_name}', log_path=str(tmp_path / 'ei.log')
    )

    # Operation log payload.
    log_mock.assert_called_once()
    logged_payload = log_mock.call_args.args[0]
    assert logged_payload['action'] == 'install'
    assert logged_payload['manager'] == 'snap'
    assert logged_payload['packages'] == [package_name]
    assert logged_payload['installed_packages'] == [package_name]

    # Success feedback to the user.
    console_mock.assert_called()
    assert package_name in console_mock.call_args.args[0]


def test_install_with_manager_failure_raises_system_exit(tmp_path):
    package_name = 'bad-app'
    log_mock = MagicMock()

    with patch.dict(
        ph.MANAGER_TO_LISTER,
        {'snap': lambda: {'base-package'}},
        clear=True,
    ):
        with patch.object(ph, 'config', {'log_dir': str(tmp_path)}):
            with patch(
                'easyinstaller.core.package_handler._ensure_manager_installed'
            ), patch(
                'easyinstaller.core.package_handler.run_cmd_smart',
                return_value=2,
            ), patch.object(
                ph.console, 'print'
            ) as console_mock, patch(
                'easyinstaller.core.package_handler.log_operation', log_mock
            ):
                with pytest.raises(SystemExit) as exc:
                    ph.install_with_manager(package_name, 'snap')

    assert exc.value.code == 2
    console_mock.assert_called()
    error_messages = [call.args[0] for call in console_mock.call_args_list]
    assert any('Error installing' in message for message in error_messages)
    assert not log_mock.called


def test_install_with_manager_multiple_packages(tmp_path):
    package_names = ['pkg-one', 'pkg-two']
    lister_states = iter(
        [
            {'base-package'},
            {'base-package', *package_names},
        ]
    )

    def fake_lister():
        return set(next(lister_states))

    log_mock = MagicMock()
    with patch.dict(ph.MANAGER_TO_LISTER, {'snap': fake_lister}, clear=True):
        with patch.object(ph, 'config', {'log_dir': str(tmp_path)}):
            with patch(
                'easyinstaller.core.package_handler._ensure_manager_installed'
            ), patch(
                'easyinstaller.core.package_handler.run_cmd_smart',
                return_value=0,
            ) as run_mock, patch.object(
                ph.console, 'print'
            ) as console_mock, patch(
                'easyinstaller.core.package_handler.log_operation', log_mock
            ):
                ph.install_with_manager(package_names, 'snap')

    run_mock.assert_called_once_with(
        'sudo snap install pkg-one pkg-two',
        log_path=str(tmp_path / 'ei.log'),
    )

    log_mock.assert_called_once()
    logged_payload = log_mock.call_args.args[0]
    assert logged_payload['packages'] == package_names
    assert logged_payload['installed_packages'] == package_names
    console_calls = [call.args[0] for call in console_mock.call_args_list]
    assert any('2 packages' in message for message in console_calls)


def test_remove_with_manager_success(tmp_path):
    package_name = 'old-app'
    lister_states = iter(
        [
            {'base-package', package_name},
            {'base-package'},
        ]
    )

    def fake_lister():
        return set(next(lister_states))

    log_mock = MagicMock()
    with patch.dict(ph.MANAGER_TO_LISTER, {'snap': fake_lister}, clear=True):
        with patch.object(ph, 'config', {'log_dir': str(tmp_path)}):
            with patch(
                'easyinstaller.core.package_handler.run_cmd_smart',
                return_value=0,
            ) as run_mock, patch.object(
                ph.console, 'print'
            ) as console_mock, patch(
                'easyinstaller.core.package_handler.log_operation', log_mock
            ):
                ph.remove_with_manager(package_name, 'snap')

    run_mock.assert_called_once_with(
        f'sudo snap remove {package_name}', log_path=str(tmp_path / 'ei.log')
    )

    logged_payload = log_mock.call_args.kwargs or log_mock.call_args.args
    logged_payload = logged_payload[0]
    assert logged_payload['action'] == 'remove'
    assert logged_payload['removed_packages'] == [package_name]
    console_mock.assert_called()
    assert package_name in console_mock.call_args.args[0]
