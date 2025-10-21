import datetime
import json
import os
import platform

import typer
from rich.console import Console

from easyinstaller.core.config import config
from easyinstaller.core.distro_detector import get_native_manager_type
from easyinstaller.core.lister import unified_lister
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='export',
    help=_('Exports a list of all installed packages to a JSON file.'),
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


@app.callback(invoke_without_command=True)
def export_packages(
    managers: list[str] = typer.Argument(
        None,
        help=_(
            'Optional: Specify one or more managers to export (e.g., apt, snap).'
        ),
    ),
    output_file: str = typer.Option(
        None,
        '--output',
        '-o',
        help=_(
            'Path to save the JSON file. Defaults to a timestamped file in ~/.local/share/easyinstaller/exports/.'
        ),
    ),
):
    """
    Gathers installed packages and system information and exports to a JSON file.
    Can be filtered by one or more package managers.
    """
    # If no output file is specified, create a default one
    if output_file is None:
        today_str = datetime.date.today().isoformat()
        export_dir = config.get('export_dir', '.')
        output_file = os.path.join(export_dir, f'setup-{today_str}.json')

    console.print(_('[bold green]Starting export...[/bold green]'))

    status_text = _('[cyan]Gathering system and package information...[/cyan]')
    if managers:
        status_text = _(
            '[cyan]Gathering info for {managers_list} packages...[/cyan]'
        ).format(managers_list=', '.join(managers))

    with console.status(status_text):
        packages = unified_lister(managers)

        os_release = get_os_release()
        system_info = {
            'distro': os_release.get('NAME', _('Unknown')),
            'version': os.get('VERSION_ID', _('Unknown')),
            'user': os.getlogin(),
            'architecture': platform.machine(),
            'native_manager': get_native_manager_type(),
        }

        export_data = {
            'type': 'export',
            'date': datetime.date.today().isoformat(),
            'system': system_info,
            'packages': {'apt': [], 'flatpak': [], 'snap': []},
        }

        # If filtering, only include the requested managers in the final dict
        if managers:
            export_data['packages'] = {
                mgr: [] for mgr in managers if mgr in export_data['packages']
            }

        for pkg in packages:
            source = pkg.get('source')
            if source in export_data['packages']:
                package_details = {
                    'name': pkg.get('name'),
                    'version': pkg.get('version'),
                    'size': pkg.get('size'),
                }
                if source == 'flatpak':
                    package_details['id'] = pkg.get('id')
                export_data['packages'][source].append(package_details)

    try:
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        console.print(_('[bold green]✔ Export successful![/bold green]'))
        console.print(
            _(
                '[white]Setup file saved to:[/] [cyan]{output_file_path}[/cyan]'
            ).format(output_file_path=os.path.abspath(output_file))
        )

    except Exception as e:
        console.print(
            _('[bold red]Error writing to file:[/bold red] {error}')
        ).format(error=e)
