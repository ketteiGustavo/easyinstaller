from __future__ import annotations

import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

import requests
import typer
from rich.console import Console
from rich.markdown import Markdown

from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='update',
    help=_('Checks for and installs updates for easyinstaller.'),
    no_args_is_help=False,
)
console = Console()

GITHUB_REPO = 'ketteiGustavo/easyinstaller'
DATA_DIR = '/usr/local/share/easyinstaller'
CHANGELOG_FILE = 'CHANGELOG.md'
LICENSE_FILE = 'LICENSE'


def get_current_version() -> str:
    """Reads the current version string from a bundled VERSION file."""
    search_paths = [
        Path(sys.executable).resolve().parent / 'easyinstaller' / 'VERSION',
        Path(__file__).resolve().parent.parent / 'VERSION',
    ]

    for path in search_paths:
        if path.is_file():
            try:
                return path.read_text(encoding='utf-8').strip()
            except OSError as error:
                console.print(
                    _(
                        '[red]Error reading current version:[/red] {error}'
                    ).format(error=error)
                )
                raise typer.Exit(1)

    console.print(_('[red]Error: Could not find VERSION file.[/red]'))
    raise typer.Exit(1)


def get_latest_release_info() -> Dict:
    """Fetches the latest release information from GitHub."""
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        console.print(
            _(
                '[red]Error fetching latest release from GitHub:[/red] {error}'
            ).format(error=error)
        )
        raise typer.Exit(1)


def compare_versions(current_v: str, latest_v: str) -> bool:
    """Returns True if the latest version is newer than the current one."""
    current_parts = list(map(int, current_v.lstrip('v').split('.')))
    latest_parts = list(map(int, latest_v.lstrip('v').split('.')))

    max_len = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    latest_parts.extend([0] * (max_len - len(latest_parts)))

    return latest_parts > current_parts


def get_system_arch() -> str:
    """Detects the libc variant of the current system."""
    if 'musl' in platform.libc_ver()[0].lower():
        return 'musl'
    return 'glibc'


def download_asset(url: str, dest_path: Path) -> None:
    """Downloads an asset to the given path when a URL is provided."""
    if not url:
        return

    console.print(
        _('Downloading [cyan]{filename}[/cyan]...').format(
            filename=dest_path.name
        )
    )
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with dest_path.open('wb') as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    handle.write(chunk)
    except requests.exceptions.RequestException as error:
        console.print(
            _('[red]Error downloading {filename}:[/red] {error}').format(
                filename=dest_path.name,
                error=error,
            )
        )
        raise typer.Exit(1)


def replace_binary(downloaded_binary_path: Path) -> None:
    """Moves the downloaded binary into place using sudo."""
    current_exe_path = Path(sys.executable)
    console.print(
        _('Replacing [cyan]{path}[/cyan] with new version...').format(
            path=current_exe_path
        )
    )

    try:
        subprocess.run(
            ['sudo', 'mv', str(downloaded_binary_path), str(current_exe_path)],
            check=True,
        )
        subprocess.run(
            ['sudo', 'chmod', '+x', str(current_exe_path)],
            check=True,
        )
        console.print('[green]✔ Binary replaced successfully.[/green]')
    except subprocess.CalledProcessError as error:
        console.print(
            _('[red]Error replacing binary:[/red] {error}').format(error=error)
        )
        console.print(
            _(
                '[red]Please try running the update command with sudo: `sudo ei update`[/red]'
            )
        )
        raise typer.Exit(1)


def _sudo_run(arguments: list[str]) -> None:
    try:
        subprocess.run(['sudo', *arguments], check=True)
    except subprocess.CalledProcessError as error:
        console.print(
            _(
                '[red]Error:[/red] Failed to run sudo command: {command}'
            ).format(command=' '.join(arguments))
        )
        raise typer.Exit(1)


def _install_with_sudo(source: Path, destination: Path) -> None:
    _sudo_run(['install', '-Dm644', str(source), str(destination)])


@app.callback(invoke_without_command=True)
def update() -> None:
    """Checks for updates and installs the latest release."""
    console.print('[bold green]Checking for updates...[/bold green]')

    current_version = get_current_version()
    console.print(
        _('Current easyinstaller version: [yellow]{version}[/yellow]').format(
            version=current_version
        )
    )

    latest_release = get_latest_release_info()
    latest_version = latest_release['tag_name']
    console.print(
        _('Latest available version: [green]{version}[/green]').format(
            version=latest_version
        )
    )

    if not compare_versions(current_version, latest_version):
        console.print(
            _(
                '[bold blue]You are already running the latest version.[/bold blue]'
            )
        )
        raise typer.Exit()

    console.print(_('[bold yellow]A new version is available![/bold yellow]'))
    if not typer.confirm(_('Do you want to update now?'), default=False):
        raise typer.Abort()

    system_arch = get_system_arch()
    console.print(
        _('Detected system architecture: [cyan]{arch}[/cyan]').format(
            arch=system_arch
        )
    )

    binary_asset_name = (
        'ei-linux-musl-amd64'
        if system_arch == 'musl'
        else 'ei-linux-glibc2.31-amd64'
    )

    download_urls: Dict[str, str] = {}
    for asset in latest_release.get('assets', []):
        download_urls[asset['name']] = asset['browser_download_url']

    if binary_asset_name not in download_urls:
        console.print(
            _(
                '[red]Error:[/red] Could not find binary asset for {arch} in latest release.'
            ).format(arch=system_arch)
        )
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        downloaded_binary = tmpdir / binary_asset_name
        downloaded_changelog = tmpdir / CHANGELOG_FILE
        downloaded_license = tmpdir / LICENSE_FILE

        download_asset(download_urls[binary_asset_name], downloaded_binary)

        if CHANGELOG_FILE in download_urls:
            download_asset(download_urls[CHANGELOG_FILE], downloaded_changelog)

        if LICENSE_FILE in download_urls:
            download_asset(download_urls[LICENSE_FILE], downloaded_license)

        replace_binary(downloaded_binary)

        _sudo_run(['mkdir', '-p', DATA_DIR])

        if downloaded_changelog.exists():
            _install_with_sudo(
                downloaded_changelog, Path(DATA_DIR) / CHANGELOG_FILE
            )

        if downloaded_license.exists():
            _install_with_sudo(
                downloaded_license, Path(DATA_DIR) / LICENSE_FILE
            )

    console.print(
        _('[bold green]✔ easyinstaller updated successfully![/bold green]')
    )

    changelog_on_disk = Path(DATA_DIR) / CHANGELOG_FILE
    if changelog_on_disk.exists():
        console.print(_("\n[bold blue]What's New:[/bold blue]"))
        console.print(Markdown(changelog_on_disk.read_text(encoding='utf-8')))

    console.print(
        _(
            'Please restart your shell or terminal for changes to take full effect.'
        )
    )
