import os
import platform
import shutil
import subprocess
import sys

import requests
import typer
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer(
    name='update',
    help='Checks for and installs updates for easyinstaller.',
    no_args_is_help=True,
)
console = Console()

GITHUB_REPO = 'ketteiGustavo/easyinstaller'
DATA_DIR = '/usr/local/share/easyinstaller'


def get_current_version() -> str:
    """
    Reads the current version from the bundled VERSION file.
    This file is created during the Nuitka build process.
    """
    # When bundled by Nuitka, the VERSION file is accessible via the package resources.
    # However, for simplicity and direct access, we assume it's in the same directory
    # as the main executable or a known path relative to it.
    # For Nuitka, --include-data-file=src/easyinstaller/VERSION=easyinstaller/VERSION
    # means it's available as easyinstaller/VERSION in the root of the bundled app.
    try:
        # This path is relative to the executable's location within the Nuitka bundle
        # or the source tree if running uncompiled.
        version_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..',
            'VERSION',
        )
        # Adjust for the actual bundled path if necessary, or use a more robust resource loading.
        # For now, assuming it's directly readable from a known relative path.
        # A more robust solution for Nuitka would be to use importlib.resources or similar.
        # For this context, let's assume it's directly readable from a known relative path.
        # If running from source, it would be src/easyinstaller/VERSION
        # If running from Nuitka onefile, it's bundled inside.
        # Let's try to read it from the expected location relative to the executable.
        # For Nuitka onefile, the data files are extracted to a temp dir.
        # The path needs to be relative to the *extracted* executable.
        # A common pattern is to put it next to the main script.

        # Let's try to read it from the current working directory first, then relative to __file__
        # This needs to be robust for both compiled and uncompiled.
        # For Nuitka, the data file is usually extracted to a temporary directory
        # alongside the executable. The path `easyinstaller/VERSION` is the target path
        # inside the bundle. When extracted, it might be `_MEIxxxxxx/easyinstaller/VERSION`
        # or similar. A simpler approach for Nuitka is to read it as a resource.

        # For now, let's assume it's directly readable from a known path relative to the executable.
        # This might need adjustment based on Nuitka's exact extraction behavior.
        # A more reliable way for Nuitka is to use `pkg_resources` or `importlib.resources`
        # but these might add dependencies or complexity.

        # Let's try a simple approach first, assuming it's placed in the same dir as the executable
        # or a predictable relative path.
        # Given --include-data-file=src/easyinstaller/VERSION=easyinstaller/VERSION
        # it means it will be at easyinstaller/VERSION relative to the bundle root.
        # If the executable is /usr/local/bin/ei, and it's a onefile, it extracts to a temp dir.
        # The VERSION file will be inside that temp dir, at easyinstaller/VERSION.
        # The current executable path is `sys.argv[0]`.

        # Let's try to read it from the current executable's directory, assuming it's extracted there.
        exe_dir = os.path.dirname(sys.executable)
        version_path_in_bundle = os.path.join(
            exe_dir, 'easyinstaller', 'VERSION'
        )

        if os.path.exists(version_path_in_bundle):
            with open(version_path_in_bundle, 'r') as f:
                return f.read().strip()
        else:
            # Fallback for development/uncompiled mode
            dev_version_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', 'VERSION'
            )
            if os.path.exists(dev_version_path):
                with open(dev_version_path, 'r') as f:
                    return f.read().strip()

        console.print('[red]Error: Could not find VERSION file.[/red]')
        raise typer.Exit(1)
    except Exception as e:
        console.print(f'[red]Error reading current version:[/red] {e}')
        raise typer.Exit(1)


def get_latest_release_info() -> dict:
    """
    Fetches the latest release information from GitHub.
    """
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(
            f'[red]Error fetching latest release from GitHub:[/red] {e}'
        )
        raise typer.Exit(1)


def compare_versions(current_v: str, latest_v: str) -> bool:
    """
    Compares two version strings (e.g., 'v0.1.0' and 'v0.1.1').
    Returns True if latest_v is newer than current_v.
    """
    # Remove 'v' prefix if present
    current_v = current_v.lstrip('v')
    latest_v = latest_v.lstrip('v')

    current_parts = list(map(int, current_v.split('.')))
    latest_parts = list(map(int, latest_v.split('.')))

    # Pad with zeros if one version has fewer parts (e.g., 1.0 vs 1.0.0)
    max_len = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    latest_parts.extend([0] * (max_len - len(latest_parts)))

    return latest_parts > current_parts


def get_system_arch() -> str:
    """
    Detects the system architecture (glibc or musl).
    """
    # Check for musl libc
    if 'musl' in platform.libc_ver()[0].lower():
        return 'musl'
    return 'glibc'


def download_asset(url: str, dest_path: str):
    """
    Downloads a file from a URL to a destination path.
    """
    console.print(f'Downloading [cyan]{os.path.basename(dest_path)}[/cyan]...')
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        console.print(
            f'[red]Error downloading {os.path.basename(dest_path)}:[/red] {e}'
        )
        raise typer.Exit(1)


def replace_binary(downloaded_binary_path: str):
    """
    Replaces the currently running executable with the new one.
    Requires sudo.
    """
    current_exe_path = (
        sys.executable
    )  # This should be the path to the running ei binary
    console.print(
        f'Replacing [cyan]{current_exe_path}[/cyan] with new version...'
    )

    try:
        # Use sudo to replace the binary
        subprocess.run(
            ['sudo', 'mv', downloaded_binary_path, current_exe_path],
            check=True,
        )
        subprocess.run(
            ['sudo', 'chmod', '+x', current_exe_path],
            check=True,
        )
        console.print('[green]✔ Binary replaced successfully.[/green]')
    except subprocess.CalledProcessError as e:
        console.print(f'[red]Error replacing binary:[/red] {e}')
        console.print(
            '[red]Please try running the update command with sudo: `sudo ei update`[/red]'
        )
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def update():
    """
    Checks for and installs updates for easyinstaller.
    """
    console.print('[bold green]Checking for updates...[/bold green]')

    current_version = get_current_version()
    console.print(
        f'Current easyinstaller version: [yellow]{current_version}[/yellow]'
    )

    latest_release = get_latest_release_info()
    latest_version = latest_release['tag_name']
    console.print(f'Latest available version: [green]{latest_version}[/green]')

    if not compare_versions(current_version, latest_version):
        console.print(
            '[bold blue]You are already running the latest version.[/bold blue]'
        )
        raise typer.Exit()

    console.print('[bold yellow]A new version is available![/bold yellow]')
    if not typer.confirm('Do you want to update now?'):
        raise typer.Abort()

    system_arch = get_system_arch()
    console.print(f'Detected system architecture: [cyan]{system_arch}[/cyan]')

    binary_asset_name = (
        f'ei-linux-musl-amd64'
        if system_arch == 'musl'
        else f'ei-linux-glibc2.31-amd64'
    )
    changelog_asset_name = 'CHANGELOG.md'
    license_asset_name = 'LICENSE'

    download_urls = {}
    for asset in latest_release['assets']:
        if asset['name'] == binary_asset_name:
            download_urls['binary'] = asset['browser_download_url']
        elif asset['name'] == changelog_asset_name:
            download_urls['changelog'] = asset['browser_download_url']
        elif asset['name'] == license_asset_name:
            download_urls['license'] = asset['browser_download_url']

    if 'binary' not in download_urls:
        console.print(
            f'[red]Error: Could not find binary asset for {system_arch} in latest release.[/red]'
        )
        raise typer.Exit(1)

    # Create a temporary directory for downloads
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        downloaded_binary_path = os.path.join(tmpdir, binary_asset_name)
        downloaded_changelog_path = os.path.join(tmpdir, changelog_asset_name)
        downloaded_license_path = os.path.join(tmpdir, license_asset_name)

        download_asset(download_urls['binary'], downloaded_binary_path)
        download_asset(
            download_urls.get('changelog', ''), downloaded_changelog_path
        )
        download_asset(
            download_urls.get('license', ''), downloaded_license_path
        )

        replace_binary(downloaded_binary_path)

        # Store changelog and license in DATA_DIR
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(downloaded_changelog_path):
            shutil.copy(
                downloaded_changelog_path,
                os.path.join(DATA_DIR, changelog_asset_name),
            )
        if os.path.exists(downloaded_license_path):
            shutil.copy(
                downloaded_license_path,
                os.path.join(DATA_DIR, license_asset_name),
            )

    console.print(
        '[bold green]✔ easyinstaller updated successfully![/bold green]'
    )

    # Display changelog
    if os.path.exists(os.path.join(DATA_DIR, changelog_asset_name)):
        console.print("\n[bold blue]What's New:[/bold blue]")
        with open(os.path.join(DATA_DIR, changelog_asset_name), 'r') as f:
            changelog_content = f.read()
        console.print(Markdown(changelog_content))

    console.print(
        'Please restart your shell or terminal for changes to take full effect.'
    )


if __name__ == '__main__':
    app()
