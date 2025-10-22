import os
import subprocess
from concurrent.futures import ThreadPoolExecutor


def list_snap_packages():
    """Lists installed Snap packages."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            ['snap', 'list'],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        lines = result.stdout.strip().split('\n')[1:]
        packages = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                packages.append(
                    {
                        'name': parts[0],
                        'version': parts[1],
                        'size': 'N/A',  # snap list does not provide size info
                        'source': 'snap',
                    }
                )
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def list_flatpak_packages():
    """Lists installed Flatpak packages."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            [
                'flatpak',
                'list',
                '--app',
                '--columns=name,application,version,size',
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        lines = result.stdout.strip().split('\n')
        packages = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 4:
                packages.append(
                    {
                        'name': parts[0],
                        'id': parts[1],
                        'version': parts[2],
                        'size': parts[3],
                        'source': 'flatpak',
                    }
                )
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def list_apt_packages():
    """Lists installed APT packages."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            [
                'dpkg-query',
                '-W',
                "-f='${Package}\t${Version}\t${Installed-Size}\t${Section}\t${Priority}\n'",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        lines = result.stdout.strip().split('\n')
        packages = []
        for line in lines:
            parts = line.replace("'", '').split('\t')
            if len(parts) >= 5:
                size_kb = int(parts[2])
                size_mb = size_kb / 1024
                size_str = f'{size_mb:.2f} MB'
                packages.append(
                    {
                        'name': parts[0],
                        'version': parts[1],
                        'size': size_str,
                        'source': 'apt',
                        'section': parts[3] or '',
                        'priority': parts[4] or '',
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
                pass

    return all_results


def get_installed_apt_packages_set() -> set:
    """Returns a set of installed apt package names."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            ['dpkg-query', '-W', "-f='${Package}\n'"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return set(result.stdout.replace("'", '').strip().split('\n'))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def get_installed_flatpak_packages_set() -> set:
    """Returns a set of installed flatpak application IDs."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            ['flatpak', 'list', '--app', '--columns=application'],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return set(result.stdout.strip().split('\n'))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def get_installed_snap_packages_set() -> set:
    """Returns a set of installed snap package names."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            ['snap', 'list'],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        lines = result.stdout.strip().split('\n')[1:]
        return {line.split()[0] for line in lines}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def get_manual_apt_packages_set() -> set:
    """Returns a set of manually installed apt packages."""
    try:
        env = dict(os.environ, LC_ALL='C')
        result = subprocess.run(
            ['apt-mark', 'showmanual'],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        packages = {pkg.strip() for pkg in result.stdout.splitlines() if pkg.strip()}
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
