import subprocess
from concurrent.futures import ThreadPoolExecutor


def list_snap_packages():
    """Lists installed Snap packages."""
    try:
        # The `snap list` command provides nicely formatted output.
        # We skip the header line with [1:]
        result = subprocess.run(
            ['snap', 'list'], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split('\n')[1:]
        packages = []
        for line in lines:
            parts = line.split()
            packages.append(
                {
                    'name': parts[0],
                    'version': parts[1],
                    'size': parts[4] if len(parts) > 4 else 'N/A',
                    'source': 'snap',
                }
            )
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def list_flatpak_packages():
    """Lists installed Flatpak packages."""
    try:
        # Flatpak allows specifying columns, which is very helpful.
        result = subprocess.run(
            ['flatpak', 'list', '--app', '--columns=name,version,size'],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split('\n')
        packages = []
        for line in lines:
            parts = line.split('\t')   # Columns are tab-separated
            if len(parts) >= 3:
                packages.append(
                    {
                        'name': parts[0],
                        'version': parts[1],
                        'size': parts[2],
                        'source': 'flatpak',
                    }
                )
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def list_apt_packages():
    """Lists installed APT packages."""
    # This is more complex as apt doesn't have a simple, clean output for this.
    # We'll use dpkg-query as it's better for scripting.
    try:
        # Get package name, version, and installed size.
        result = subprocess.run(
            [
                'dpkg-query',
                '-W',
                "-f='${Package}\t${Version}\t${Installed-Size}\n'",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split('\n')
        packages = []
        for line in lines:
            parts = line.replace("'", '').split('\t')
            if len(parts) >= 3:
                # Convert size from KB to a human-readable format
                size_kb = int(parts[2])
                size_mb = size_kb / 1024
                size_str = f'{size_mb:.2f} MB'
                packages.append(
                    {
                        'name': parts[0],
                        'version': parts[1],
                        'size': size_str,
                        'source': 'apt',
                    }
                )
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return []


def unified_lister(managers: list[str] | None = None):
    """Performs listing across specified managers in parallel, or all if none specified."""
    if managers is None:
        managers = ['apt', 'flatpak', 'snap']

    source_map = {
        'apt': list_apt_packages,
        'flatpak': list_flatpak_packages,
        'snap': list_snap_packages,
    }

    with ThreadPoolExecutor() as executor:
        # Only submit jobs for the requested managers
        futures = {
            executor.submit(source_map[manager])
            for manager in managers
            if manager in source_map
        }

        all_results = []
        for future in futures:
            try:
                all_results.extend(future.result())
            except Exception:
                # In a real app, you'd log this error
                pass

    return all_results
