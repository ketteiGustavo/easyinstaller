from __future__ import annotations

import os
from datetime import datetime

from rich.console import Console

from easyinstaller.core.config import config
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


def _get_native_cmd(action: str, purge: bool = False) -> str:
    native_manager = get_native_manager_type()
    if native_manager == 'unknown':
        raise ValueError(_('Unsupported native package manager.'))

    if native_manager == 'apt' and action == 'remove' and purge:
        return MANAGER_CMDS['apt']['purge']

    return MANAGER_CMDS[native_manager][action]


def _build_cmd(
    manager: str, action: str, package: str, purge: bool = False
) -> str:
    if manager == 'apt':
        base = _get_native_cmd(action, purge)
    elif manager in MANAGER_CMDS:
        base = MANAGER_CMDS[manager][action]
    else:
        raise ValueError(_(f'Unsupported manager: {manager}'))

    return f'{base} {package}'


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
    log_path = os.path.join(config['log_dir'], 'ei.log')

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


def install_with_manager(package_name: str, manager: str):
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

    # Ensure flathub remote exists to avoid interactive prompt
    if manager == 'flatpak':
        run_cmd_smart(
            'flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo'
        )

    cmd = _build_cmd(manager, 'install', package_name)
    log_path = os.path.join(config['log_dir'], 'ei.log')

    before_set = lister_func()
    code = run_cmd_smart(cmd, log_path=log_path)

    if code != 0:
        console.print(
            _(
                '[bold red]Error installing {package_name} (manager: {manager}, exit code: {code}).[/bold red]'
            ).format(package_name=package_name, manager=manager, code=code)
        )
        console.print(
            _('Check the log for details: {log_path}').format(
                log_path=log_path
            )
        )
        raise SystemExit(code)

    after_set = lister_func()
    newly_installed = sorted(list(after_set - before_set))

    if not newly_installed:
        console.print(
            _(
                '[bold yellow]Package {package_name} is already installed or no changes were detected.[/bold yellow]'
            ).format(package_name=package_name)
        )
        return

    log_operation(
        {
            'action': 'install',
            'package': package_name,
            'manager': manager,
            'timestamp': datetime.now().isoformat(),
            'installed_packages': newly_installed,
        }
    )

    dep_count = len(newly_installed) - 1
    dep_text = (
        _('with {dep_count} dependencies').format(dep_count=dep_count)
        if dep_count > 0
        else ''
    )
    console.print(
        _(
            '[bold green]✔ Successfully installed {package_name}[/] {dep_text}'
        ).format(package_name=package_name, dep_text=dep_text)
    )
