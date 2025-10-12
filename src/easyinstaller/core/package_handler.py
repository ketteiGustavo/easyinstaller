import subprocess

import typer
from rich.console import Console

from easyinstaller.core.distro_detector import get_distro_id

console = Console()

PACKAGE_MANAGERS = {
    # Debian/Ubuntu based
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
    # Arch based
    'arch': {
        'install': 'sudo pacman -S --noconfirm',
        'remove': 'sudo pacman -Rns --noconfirm',
    },
    'manjaro': {
        'install': 'sudo pacman -S --noconfirm',
        'remove': 'sudo pacman -Rns --noconfirm',
    },
    # Fedora/CentOS/RHEL based
    'fedora': {
        'install': 'sudo dnf install -y',
        'remove': 'sudo dnf remove -y',
    },
}


def get_package_manager_commands() -> dict | None:
    """Gets the command set for the current distribution."""
    distro_id = get_distro_id()
    return PACKAGE_MANAGERS.get(distro_id)


def install_package(package_name: str):
    """Constructs and prints the installation command for a given package."""
    commands = get_package_manager_commands()

    if not commands:
        console.print(
            f'[red]Error:[/red] Unsupported distribution: {get_distro_id()}'
        )
        raise typer.Exit(1)

    command = f"{commands['install']} {package_name}"
    console.print(
        f"[bold green]>>>[/bold green] Pretending to run: '[cyan]{command}[/cyan]'"
    )


def remove_package(package_name: str):
    """Constructs and prints the removal command for a given package."""
    commands = get_package_manager_commands()

    if not commands:
        console.print(
            f'[red]Error:[/red] Unsupported distribution: {get_distro_id()}'
        )
        raise typer.Exit(1)

    command = f"{commands['remove']} {package_name}"
    console.print(
        f"[bold red]>>>[/bold red] Pretending to run: '[cyan]{command}[/cyan]'"
    )


def install_with_manager(package_name: str, manager: str):
    """Constructs and prints the installation command for a given package using a specific manager."""
    if manager == 'flatpak':
        command = f'flatpak install flathub {package_name} -y'
    elif manager == 'snap':
        command = f'sudo snap install {package_name}'
    else:
        # Check if the specified manager is the native one
        commands = get_package_manager_commands()
        if commands and manager in commands['install']:
            command = f"{commands['install']} {package_name}"
        else:
            console.print(
                f'[red]Error:[/red] Unsupported or unknown manager: {manager}'
            )
            raise typer.Exit(1)

    console.print(
        f"[bold green]>>>[/bold green] Pretending to run: '[cyan]{command}[/cyan]'"
    )
