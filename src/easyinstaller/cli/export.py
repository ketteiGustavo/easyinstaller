import datetime
import json
import os
import platform

import typer
from rich.console import Console

from easyinstaller.core.distro_detector import get_native_manager_type
from easyinstaller.core.lister import unified_lister

console = Console()

app = typer.Typer(
    name='export',
    help='Export all installed packages to a JSON file.',
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
        help='Optional: Specify one or more managers to export (e.g., apt, snap).',
    ),
    output_file: str = typer.Option(
        'myapp/setup.json',
        '--output',
        '-o',
        help='The path to save the JSON file.',
    ),
):
    """
    Gathers installed packages and system information and exports to a JSON file.
    Can be filtered by one or more package managers.
    """
    console.print(f'[bold green]Starting export...[/bold green]')

    status_text = '[cyan]Gathering system and package information...[/cyan]'
    if managers:
        status_text = f"[cyan]Gathering info for { ', '.join(managers) } packages...[/cyan]"

    with console.status(status_text):
        packages = unified_lister(managers)

        os_release = get_os_release()
        system_info = {
            'distro': os_release.get('NAME', 'Unknown'),
            'version': os_release.get('VERSION_ID', 'Unknown'),
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
                export_data['packages'][source].append(package_details)

    try:
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        console.print(f'[bold green]✔ Export successful![/bold green]')
        console.print(
            f'[white]Setup file saved to:[/] [cyan]{os.path.abspath(output_file)}[/cyan]'
        )

    except Exception as e:
        console.print(f'[bold red]Error writing to file:[/bold red] {e}')
