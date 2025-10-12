import platform
from functools import lru_cache


@lru_cache(maxsize=1)
def get_distro_id() -> str:
    """Detects the Linux distribution ID.

    Uses platform.freedesktop_os_release() to get the ID from /etc/os-release.

    Returns:
        The distribution ID (e.g., 'ubuntu', 'debian', 'fedora', 'arch').
    """
    try:
        release_info = platform.freedesktop_os_release()
        return release_info.get('ID', '').lower()
    except OSError:
        # This can happen if /etc/os-release doesn't exist
        return 'unknown'
