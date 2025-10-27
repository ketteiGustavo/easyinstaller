import platform
from functools import lru_cache

# Mapping of distribution IDs to their native package manager type
DISTRO_TO_MANAGER = {
    'ubuntu': 'apt',
    'debian': 'apt',
    'linuxmint': 'apt',
    'zorin': 'apt',
    'arch': 'pacman',
    'manjaro': 'pacman',
    'fedora': 'dnf',
}


@lru_cache(maxsize=1)
def get_distro_id() -> str:
    """Detects the Linux distribution ID."""
    try:
        release_info = platform.freedesktop_os_release()
        return release_info.get('ID', '').lower()
    except OSError:
        return 'unknown'


@lru_cache(maxsize=1)
def get_native_manager_type() -> str:
    """Gets the native package manager type (apt, dnf, pacman) for the current distro."""
    distro_id = get_distro_id()
    return DISTRO_TO_MANAGER.get(distro_id, 'unknown')
