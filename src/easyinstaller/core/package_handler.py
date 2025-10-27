from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from datetime import datetime
from typing import Sequence

from rich.console import Console

from easyinstaller.core.config import config, default_paths
from easyinstaller.core.distro_detector import get_native_manager_type
from easyinstaller.core.history_handler import log_operation
from easyinstaller.core.lister import (
    get_installed_apt_packages_set,
    get_installed_flatpak_packages_set,
    get_installed_snap_packages_set,
)
from easyinstaller.core.runner import run_cmd_smart
from easyinstaller.i18n.i18n import _

console = Console()

# Centralized command definitions
MANAGER_CMDS = {
    'apt': {
        'install': 'sudo -E apt-get install -y',
        'remove': 'sudo -E apt-get remove -y',
        'purge': 'sudo -E apt-get purge -y',
    },
    'pacman': {
        'install': 'sudo pacman -S --noconfirm',
        'remove': 'sudo pacman -Rns --noconfirm',
    },
    'dnf': {
        'install': 'sudo dnf install -y',
        'remove': 'sudo dnf remove -y',
    },
    'flatpak': {
        'install': 'flatpak install -y flathub',
        'remove': 'flatpak uninstall -y',
    },
    'snap': {
        'install': 'sudo snap install',
        'remove': 'sudo snap remove',
    },
}

MANAGER_TO_LISTER = {
    'apt': get_installed_apt_packages_set,
    'flatpak': get_installed_flatpak_packages_set,
    'snap': get_installed_snap_packages_set,
}


def _get_log_file_path() -> str:
    """
    Returns the absolute path to the default log file, ensuring the directory exists.
    Falls back to default paths if configuration keys are missing.
    """
    log_dir = (
        config.get('log_path')
        or config.get('log_dir')
        or default_paths().get('log_path')
    )

    if not log_dir:
        raise RuntimeError('Unable to determine log directory path.')

    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'ei.log')


def prime_sudo_session() -> bool:
    """
    Runs `sudo -v` to refresh the user's sudo timestamp.
    This should be called before a batch of operations requiring sudo.
    Returns True if successful or not needed, False on failure.
    """
    if os.geteuid() == 0:
        return True

    console.print(_('[cyan]Refreshing sudo credentials...[/cyan]'))
    returncode = run_cmd_smart('sudo -v')
    if returncode != 0:
        console.print(
            _(
                '[yellow]Could not refresh sudo credentials. You may be prompted for a password multiple times.[/yellow]'
            )
        )
        return False
    console.print('[green]Sudo credentials refreshed.[/green]')
    return True


def _get_native_cmd(action: str, purge: bool = False) -> str:
    native_manager = get_native_manager_type()
    if native_manager == 'unknown':
        raise ValueError(_('Unsupported native package manager.'))

    if native_manager == 'apt' and action == 'remove' and purge:
        return MANAGER_CMDS['apt']['purge']

    return MANAGER_CMDS[native_manager][action]


def _build_cmd(
    manager: str,
    action: str,
    packages: str | Sequence[str],
    purge: bool = False,
) -> str:
    if manager == 'apt':
        base = _get_native_cmd(action, purge)
    elif manager in MANAGER_CMDS:
        base = MANAGER_CMDS[manager][action]
    else:
        raise ValueError(_(f'Unsupported manager: {manager}'))

    if isinstance(packages, str):
        package_list = [packages]
    else:
        package_list = [pkg for pkg in packages if pkg]

    if not package_list:
        raise ValueError(_('No packages specified for command execution.'))

    quoted_packages = ' '.join(shlex.quote(pkg) for pkg in package_list)
    return f'{base} {quoted_packages}'


def _ensure_manager_installed(manager_to_check: str):
    """Checks if flatpak or snap are installed and tries to install them if not."""
    if shutil.which(manager_to_check):
        return

    native_manager = get_native_manager_type()
    if native_manager == 'unknown':
        console.print(
            _(
                '[yellow]Warning:[/] Cannot automatically install {manager_to_check} as the native package manager is unknown.'
            ).format(manager_to_check=manager_to_check)
        )
        return

    package_to_install = {'flatpak': 'flatpak', 'snap': 'snapd'}.get(
        manager_to_check
    )
    if not package_to_install:
        return

    console.print(
        _(
            "[cyan]Package manager '{manager_to_check}' not found. Attempting to install it with {native_manager}...[/cyan]"
        ).format(
            manager_to_check=manager_to_check, native_manager=native_manager
        )
    )

    cmd = _build_cmd(native_manager, 'install', package_to_install)
    log_path = _get_log_file_path()
    code = run_cmd_smart(cmd, log_path=log_path)

    if code != 0:
        console.print(
            _(
                '[red]Error:[/] Failed to install {manager_to_check}. Please install it manually and try again.'
            ).format(manager_to_check=manager_to_check)
        )
        raise SystemExit(code)

    console.print(
        _('✔ Successfully installed {manager_to_check}.').format(
            manager_to_check=manager_to_check
        )
    )


def remove_with_manager(package_name: str, manager: str, purge: bool = False):
    lister_func = MANAGER_TO_LISTER.get(manager) or MANAGER_TO_LISTER.get(
        get_native_manager_type()
    )
    if not lister_func:
        console.print(
            _(
                '[red]Error:[/red] No lister function found for manager: {manager}'
            ).format(manager=manager)
        )
        raise SystemExit(1)

    cmd = _build_cmd(manager, 'remove', package_name, purge=purge)
    log_path = _get_log_file_path()

    before_set = lister_func()
    code = run_cmd_smart(cmd, log_path=log_path)

    if code != 0:
        console.print(
            _(
                '[bold red]Error removing {package_name} (manager: {manager}, exit code: {code}).[/bold red]'
            ).format(package_name=package_name, manager=manager, code=code)
        )
        console.print(
            _('Check the log for details: {log_path}').format(
                log_path=log_path
            )
        )
        raise SystemExit(code)

    after_set = lister_func()
    removed_packages = sorted(list(before_set - after_set))

    # If nothing was removed, it might be because the package didn't exist
    if not removed_packages:
        console.print(
            _(
                '[bold yellow]Package {package_name} was not installed or no changes were detected.[/bold yellow]'
            ).format(package_name=package_name)
        )
        return

    log_operation(
        {
            'action': 'remove',
            'package': package_name,
            'manager': manager,
            'timestamp': datetime.now().isoformat(),
            'removed_packages': removed_packages,
        }
    )

    console.print(
        _(
            '[bold green]✔ Successfully removed {package_name}.[/bold green]'
        ).format(package_name=package_name)
    )


def install_with_manager(package_names: str | Sequence[str], manager: str):
    if isinstance(package_names, str):
        package_list = [package_names]
    else:
        package_list = [pkg for pkg in package_names if pkg]

    if not package_list:
        console.print(
            _('[yellow]No packages were provided for installation.[/yellow]')
        )
        return

    lister_func = MANAGER_TO_LISTER.get(manager) or MANAGER_TO_LISTER.get(
        get_native_manager_type()
    )

    if not lister_func:
        console.print(
            _(
                '[red]Error:[/red] No lister function found for manager: {manager}'
            ).format(manager=manager)
        )
        raise SystemExit(1)

    if manager in ('flatpak', 'snap'):
        _ensure_manager_installed(manager)

    # Ensure flathub remote exists to avoid interactive prompt
    if manager == 'flatpak':
        run_cmd_smart(
            'flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo'
        )

    cmd = _build_cmd(manager, 'install', package_list)
    log_path = _get_log_file_path()

    before_set = lister_func()
    code = run_cmd_smart(cmd, log_path=log_path)

    if code != 0:
        console.print(
            _(
                '[bold red]Error installing {package_name} (manager: {manager}, exit code: {code}).[/bold red]'
            ).format(
                package_name=', '.join(package_list),
                manager=manager,
                code=code,
            )
        )
        console.print(
            _('Check the log for details: {log_path}').format(
                log_path=log_path
            )
        )
        raise SystemExit(code)

    after_set = lister_func()
    newly_installed = sorted(list(after_set - before_set))
    package_label = (
        package_list[0]
        if len(package_list) == 1
        else _('{} packages').format(len(package_list))
    )

    if not newly_installed:
        console.print(
            _(
                '[bold yellow]{package_name} is already installed or no changes were detected.[/bold yellow]'
            ).format(package_name=package_label)
        )
        return

    payload = {
        'action': 'install',
        'manager': manager,
        'timestamp': datetime.now().isoformat(),
        'packages': package_list,
        'installed_packages': newly_installed,
    }
    if len(package_list) == 1:
        payload['package'] = package_list[0]

    log_operation(payload)

    requested_set = set(package_list)
    dep_count = len(
        [pkg for pkg in newly_installed if pkg not in requested_set]
    )
    dep_text = (
        _('with {dep_count} dependencies').format(dep_count=dep_count)
        if dep_count > 0
        else ''
    )
    console.print(
        _(
            '[bold green]✔ Successfully installed {package_name}[/] {dep_text}'
        ).format(package_name=package_label, dep_text=dep_text)
    )
