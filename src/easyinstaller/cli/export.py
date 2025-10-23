import datetime
import json
import os
import platform
from typing import Dict, Iterable, List, Optional, Sequence

import typer
from rich.console import Console

from easyinstaller.core.config import config
from easyinstaller.core.distro_detector import get_native_manager_type
from easyinstaller.core.favorites import favorites_count, load_favorites
from easyinstaller.core.lister import unified_lister
from easyinstaller.core.package_filters import (
    DEFAULT_MANAGERS,
    filter_user_app_packages,
    group_packages_by_manager,
)
from easyinstaller.i18n.i18n import _

console = Console()

DEFAULT_FILE_PREFIX = {
    'full': 'setup',
    'apps': 'apps',
    'favorites': 'favorites',
}

VALID_MANAGERS = {'apt', 'flatpak', 'snap'}

app = typer.Typer(
    name='export',
    help=_('Exports lists of applications or full system setups to JSON.'),
)


def get_os_release():
    """Parses /etc/os-release to get distribution info."""
    release_info = {}
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    release_info[key] = value.strip('"')
    except FileNotFoundError:
        return {}
    return release_info


def normalize_managers(managers: Optional[Sequence[str]]) -> List[str]:
    if not managers:
        return []
    normalized = []
    for manager in managers:
        key = manager.lower()
        if key not in VALID_MANAGERS:
            raise typer.BadParameter(
                _(
                    'Invalid manager "[yellow]{manager}[/yellow]". Choose from: {choices}'
                ).format(
                    manager=manager,
                    choices=', '.join(sorted(VALID_MANAGERS)),
                )
            )
        if key not in normalized:
            normalized.append(key)
    return normalized


def iter_package_payload(packages: Iterable[Dict]) -> Iterable[Dict]:
    for pkg in packages:
        item = {
            'name': pkg.get('name'),
            'version': pkg.get('version'),
            'size': pkg.get('size'),
        }
        if pkg.get('source') == 'flatpak':
            item['id'] = pkg.get('id')
        yield item


def build_system_info() -> Dict:
    os_release = get_os_release()
    return {
        'distro': os_release.get('NAME', _('Unknown')),
        'version': os_release.get('VERSION_ID', _('Unknown')),
        'user': os.getlogin(),
        'architecture': platform.machine(),
        'native_manager': get_native_manager_type(),
    }


def default_output_path(mode: str) -> str:
    today_str = datetime.date.today().isoformat()
    export_dir = config.get('export_dir', '.')
    prefix = DEFAULT_FILE_PREFIX.get(mode, 'export')
    return os.path.join(export_dir, f'{prefix}-{today_str}.json')


def ensure_output_directory(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def write_export_file(path: str, data: Dict) -> None:
    ensure_output_directory(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def perform_export(
    mode: str,
    managers: Optional[List[str]],
    output_file: Optional[str],
) -> None:
    selected_managers = normalize_managers(managers)
    output_path = output_file or default_output_path(mode)

    if mode == 'favorites':
        favorites = load_favorites()
        if favorites_count(favorites) == 0:
            console.print(
                _(
                    '[yellow]No favorites defined yet. Use `ei favorites` to create your list.[/yellow]'
                )
            )
            raise typer.Exit(0)
        if selected_managers:
            favorites = {
                manager: favorites.get(manager, [])
                for manager in selected_managers
            }
        export_data = {
            'type': 'export_favorites',
            'date': datetime.date.today().isoformat(),
            'system': build_system_info(),
            'packages': favorites,
        }
    else:
        console.print(_('[bold green]Starting export...[/bold green]'))

        managers_to_use = selected_managers or list(DEFAULT_MANAGERS)
        status_text = _(
            '[cyan]Gathering info for {managers_list} packages...[/cyan]'
        ).format(managers_list=', '.join(managers_to_use))

        with console.status(status_text):
            packages = unified_lister(managers_to_use)
            if mode == 'apps':
                packages = filter_user_app_packages(packages)

            grouped = group_packages_by_manager(packages, managers_to_use)
            packages_payload = {
                manager: list(iter_package_payload(entries))
                for manager, entries in grouped.items()
            }

            export_type = 'export_apps' if mode == 'apps' else 'export_full'
            export_data = {
                'type': export_type,
                'date': datetime.date.today().isoformat(),
                'system': build_system_info(),
                'packages': packages_payload,
            }

            if mode == 'full':
                export_data['system'] = build_system_info()

    try:
        write_export_file(output_path, export_data)
        console.print(_('[bold green]✔ Export successful![/bold green]'))
        console.print(
            _(
                '[white]Export saved to:[/] [cyan]{output_file_path}[/cyan]'
            ).format(output_file_path=os.path.abspath(output_path))
        )
    except OSError as error:
        console.print(
            _('[bold red]Error writing to file:[/bold red] {error}').format(
                error=error
            )
        )


@app.callback(invoke_without_command=True)
def export_root(ctx: typer.Context):
    """
    Default behaviour mirrors `ei export full`.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(full)


@app.command('full')
def full(
    managers: Optional[List[str]] = typer.Option(
        None,
        '--manager',
        '-m',
        help=_('Optional package managers to include (apt, flatpak, snap).'),
    ),
    output: Optional[str] = typer.Option(
        None,
        '--output',
        '-o',
        help=_(
            'Path to save the JSON file. Defaults to ~/.local/share/easyinstaller/exports/ with a mode-based name.'
        ),
    ),
):
    """
    Export system information plus all installed packages.
    """
    perform_export('full', managers, output)


@app.command('apps')
def apps(
    managers: Optional[List[str]] = typer.Option(
        None,
        '--manager',
        '-m',
        help=_('Optional package managers to include (apt, flatpak, snap).'),
    ),
    output: Optional[str] = typer.Option(
        None,
        '--output',
        '-o',
        help=_(
            'Path to save the JSON file. Defaults to ~/.local/share/easyinstaller/exports/ with a mode-based name.'
        ),
    ),
):
    """
    Export user-focused applications, excluding distro components.
    """
    perform_export('apps', managers, output)


@app.command('favorites')
def favorites_export(
    managers: Optional[List[str]] = typer.Option(
        None,
        '--manager',
        '-m',
        help=_('Optional package managers to include (apt, flatpak, snap).'),
    ),
    output: Optional[str] = typer.Option(
        None,
        '--output',
        '-o',
        help=_(
            'Path to save the JSON file. Defaults to ~/.local/share/easyinstaller/exports/ with a mode-based name.'
        ),
    ),
):
    """
    Export the saved favorites list.
    """
    perform_export('favorites', managers, output)
