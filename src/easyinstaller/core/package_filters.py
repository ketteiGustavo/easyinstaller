from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Sequence

from easyinstaller.core.lister import get_manual_apt_packages_set

DEFAULT_MANAGERS = ('apt', 'flatpak', 'snap')

APT_SYSTEM_PRIORITIES = {
    'required',
    'important',
    'standard',
    'essential',
}

APT_SYSTEM_SECTION_PREFIXES = (
    'admin',
    'cli-mono',
    'debug',
    'debian-installer',
    'dev',
    'doc',
    'gnome-shell',
    'gnome',
    'graphics-drivers',
    'i18n',
    'introspection',
    'kernel',
    'lib',
    'libs',
    'localization',
    'oldlibs',
    'perl',
    'php',
    'python',
    'rust',
    'science',
    'shells',
    'system',
    'translations',
    'utils',
    'web',
    'x11',
)

APT_SYSTEM_PACKAGE_NAMES = {
    'base-files',
    'base-passwd',
    'bash',
    'ca-certificates',
    'coreutils',
    'dpkg',
    'gcc',
    'gcc-12-base',
    'gcc-13-base',
    'init',
    'libc6',
    'login',
    'mount',
    'passwd',
    'systemd',
    'systemd-timesyncd',
    'tzdata',
    'ubuntu-desktop',
    'ubuntu-minimal',
    'ubuntu-standard',
}

SNAP_SYSTEM_PACKAGES = {
    'bare',
    'core',
    'core18',
    'core20',
    'core22',
    'gnome-3-28-1804',
    'gnome-3-38-2004',
    'gtk-common-themes',
    'snapd',
}


def is_system_apt_package(pkg: Dict) -> bool:
    name = (pkg.get('name') or '').lower()
    if name in APT_SYSTEM_PACKAGE_NAMES:
        return True

    priority = (pkg.get('priority') or '').lower()
    if priority in APT_SYSTEM_PRIORITIES:
        return True

    section = (pkg.get('section') or '').lower()
    for prefix in APT_SYSTEM_SECTION_PREFIXES:
        if section.startswith(prefix):
            return True

    return False


def filter_user_app_packages(packages: Sequence[Dict]) -> List[Dict]:
    manual_apt_packages = get_manual_apt_packages_set()
    filtered: List[Dict] = []

    for pkg in packages:
        manager = pkg.get('source')
        if manager == 'apt':
            name = pkg.get('name')
            if manual_apt_packages and name not in manual_apt_packages:
                continue
            if is_system_apt_package(pkg):
                continue
        elif manager == 'snap':
            name = pkg.get('name')
            if name in SNAP_SYSTEM_PACKAGES:
                continue
        filtered.append(pkg)

    return filtered


def group_packages_by_manager(
    packages: Iterable[Dict], managers: Sequence[str] | None = None
) -> Dict[str, List[Dict]]:
    manager_keys = [m for m in (managers or DEFAULT_MANAGERS)]
    grouped = defaultdict(list)
    for key in manager_keys:
        grouped[key]  # initialize

    for pkg in packages:
        manager = pkg.get('source')
        if manager_keys and manager not in manager_keys:
            continue
        grouped[manager].append(pkg)

    return {manager: grouped.get(manager, []) for manager in manager_keys}
