import subprocess
from datetime import datetime

import typer
from rich.console import Console

from easyinstaller.core.distro_detector import get_distro_id
from easyinstaller.core.history_handler import log_operation
from easyinstaller.core.lister import (
    get_installed_apt_packages_set,
    get_installed_flatpak_packages_set,
    get_installed_snap_packages_set,
)

console = Console()

PACKAGE_MANAGERS = {
    'ubuntu': {
        'install': 'sudo apt install -y',
        'remove': 'sudo apt remove -y',
    },
    'debian': {
        'install': 'sudo apt install -y',
        'remove': 'sudo apt remove -y',
    },
    'linuxmint': {
        'install': 'sudo apt install -y',
        'remove': 'sudo apt remove -y',
    },
    'arch': {
        'install': 'sudo pacman -S --noconfirm',
        'remove': 'sudo pacman -Rns --noconfirm',
    },
    'manjaro': {
        'install': 'sudo pacman -S --noconfirm',
        'remove': 'sudo pacman -Rns --noconfirm',
    },
    'fedora': {
        'install': 'sudo dnf install -y',
        'remove': 'sudo dnf remove -y',
    },
}

MANAGER_TO_LISTER = {
    'apt': get_installed_apt_packages_set,
    'flatpak': get_installed_flatpak_packages_set,
    'snap': get_installed_snap_packages_set,
}


def get_package_manager_commands() -> dict | None:
    distro_id = get_distro_id()
    return PACKAGE_MANAGERS.get(distro_id)


def remove_with_manager(package_name: str, manager: str, purge: bool = False):
    """Constructs and executes the removal command for a given package using a specific manager."""
    command_str = ''
    if manager == 'flatpak':
        command_str = f'flatpak uninstall {package_name} -y'
    elif manager == 'snap':
        command_str = f'sudo snap remove {package_name}'
    else:
        commands = get_package_manager_commands()
        if commands and (
            manager in commands['remove'] or manager in commands['install']
        ):
            base_command = commands['remove']
            if purge and 'apt' in base_command:
                base_command = base_command.replace('remove', 'purge')
            command_str = f'{base_command} {package_name}'
        else:
            console.print(
                f'[red]Error:[/red] Unsupported or unknown manager: {manager}'
            )
            raise typer.Exit(1)

    if command_str:
        with console.status(f'[bold cyan]Running command:[/] {command_str}'):
            try:
                subprocess.run(
                    command_str.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                console.print(
                    f'[bold red]Error removing {package_name}.[/bold red]'
                )
                console.print(f'[white]STDOUT:[/] {e.stdout}')
                console.print(f'[white]STDERR:[/] {e.stderr}')
                raise typer.Exit(1)
        console.print(
            f'[bold green]✔ Successfully removed {package_name}.[/bold green]'
        )


def install_with_manager(package_name: str, manager: str):
    """Constructs and executes the installation command, logging the operation and dependencies."""
    command_str = ''
    lister_func = MANAGER_TO_LISTER.get(manager)
    # For native managers, we might use a different lister key
    if not lister_func:
        native_distro = get_distro_id()
        if native_distro in ['ubuntu', 'debian', 'linuxmint']:
            lister_func = MANAGER_TO_LISTER.get('apt')

    if not lister_func:
        console.print(
            f'[red]Error:[/red] No lister function found for manager: {manager}'
        )
        raise typer.Exit(1)

    if manager == 'flatpak':
        command_str = f'flatpak install flathub {package_name} -y'
    elif manager == 'snap':
        command_str = f'sudo snap install {package_name}'
    else:
        commands = get_package_manager_commands()
        if commands and (
            manager in commands['remove'] or manager in commands['install']
        ):
            command_str = f"{commands['install']} {package_name}"
        else:
            console.print(
                f'[red]Error:[/red] Unsupported or unknown manager: {manager}'
            )
            raise typer.Exit(1)

    if command_str:
        before_set = lister_func()
        with console.status(f'[bold cyan]Running command:[/] {command_str}'):
            try:
                subprocess.run(
                    command_str.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                console.print(
                    f'[bold red]Error installing {package_name}.[/bold red]'
                )
                console.print(f'[white]STDOUT:[/] {e.stdout}')
                console.print(f'[white]STDERR:[/] {e.stderr}')
                raise typer.Exit(1)

        after_set = lister_func()
        newly_installed = sorted(list(after_set - before_set))

        if not newly_installed:
            console.print(
                f'[bold yellow]Package {package_name} is already installed.[/bold yellow]'
            )
            return

        operation_data = {
            'action': 'install',
            'package': package_name,
            'manager': manager,
            'timestamp': datetime.now().isoformat(),
            'installed_packages': newly_installed,
        }
        log_operation(operation_data)

        dep_count = len(newly_installed) - 1
        dep_text = f'with {dep_count} dependencies' if dep_count > 0 else ''
        console.print(
            f'[bold green]✔ Successfully installed {package_name}[/] {dep_text}'
        )
