from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import requests

# NOTE: kept compatible for str importers; `DATA_DIR` used elsewhere.
GITHUB_REPO = 'ketteiGustavo/easyinstaller'
DATA_DIR = Path('/usr/local/share/easyinstaller')
PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def get_installed_version() -> str:
    """
    Returns the installed EasyInstaller version string.
    Raises FileNotFoundError if no VERSION file is found.
    """
    candidates = [
        DATA_DIR / 'VERSION',
        Path(sys.executable).resolve().parent / 'easyinstaller' / 'VERSION',
        PACKAGE_ROOT / 'VERSION',
    ]

    last_error: Exception | None = None
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            return candidate.read_text(encoding='utf-8').strip()
        except OSError as error:
            last_error = error
            break

    if last_error is not None:
        raise RuntimeError(str(last_error)) from last_error
    raise FileNotFoundError('VERSION file not found.')


def fetch_latest_release_info(timeout: int = 30) -> Dict:
    """
    Fetches the latest release information from GitHub.
    Raises requests.exceptions.RequestException on network issues.
    """
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
    response = requests.get(api_url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def compare_versions(current_v: str, latest_v: str) -> bool:
    """
    Returns True if the latest version is newer than the current one.
    Version strings may optionally start with 'v'.
    """
    current_parts = list(map(int, current_v.lstrip('v').split('.')))
    latest_parts = list(map(int, latest_v.lstrip('v').split('.')))

    max_len = max(len(current_parts), len(latest_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    latest_parts.extend([0] * (max_len - len(latest_parts)))

    return latest_parts > current_parts
