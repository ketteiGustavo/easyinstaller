import subprocess
from concurrent.futures import ThreadPoolExecutor

import requests


def unified_search(query: str) -> list[dict]:
    """Performs a search across apt, flathub, and snapcraft in parallel and sorts by relevance."""
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(search_apt, query),
            executor.submit(search_flathub, query),
            executor.submit(search_snap, query),
        ]

        all_results = []
        for future in futures:
            try:
                all_results.extend(future.result())
            except Exception as e:
                # In a real app, you'd log this error
                print(f'Error during search: {e}')

    # Sort results by relevance
    def sort_key(result):
        name = result['name'].lower()
        lower_query = query.lower()
        if name == lower_query:
            return (0, name)  # Exact match
        elif name.startswith(lower_query):
            return (1, name)  # Starts with query
        else:
            return (2, name)  # Contains query

    all_results.sort(key=sort_key)

    return all_results


def search_flathub(query: str) -> list[dict]:
    """Searches for a package on Flathub."""
    try:
        response = requests.get(
            f'https://flathub.org/api/v2/compat/apps/search/{query}'
        )
        response.raise_for_status()
        apps = response.json()
        if not isinstance(apps, list):
            return []   # API returned something other than a list
        return [
            {
                'id': app.get('flatpakAppId'),
                'name': app.get('name'),
                'summary': app.get('summary'),
                'source': 'flatpak',
            }
            for app in apps
            if isinstance(app, dict)
        ]
    except requests.RequestException:
        return []


def search_snap(query: str) -> list[dict]:
    """Searches for a package on Snapcraft."""
    try:
        response = requests.get(
            f'https://api.snapcraft.io/api/v1/snaps/search?q={query}'
        )
        response.raise_for_status()
        snaps = response.json()
        if not isinstance(snaps, list):
            return []   # API returned something other than a list
        return [
            {
                'id': snap.get('name').split('.')[0],
                'name': snap.get('name').split('.')[0],
                'summary': snap.get('summary'),
                'source': 'snap',
            }
            for snap in snaps
            if isinstance(snap, dict) and snap.get('name')
        ]
    except requests.RequestException:
        return []


def search_apt(query: str) -> list[dict]:
    """Searches for a package using apt-cache."""
    try:
        result = subprocess.run(
            ['apt-cache', 'search', '--names-only', query],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split('\n')
        results = []
        for line in lines:
            if not line:
                continue
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                results.append(
                    {
                        'id': parts[0].strip(),
                        'name': parts[0].strip(),
                        'summary': parts[1].strip(),
                        'source': 'apt',
                    }
                )
        return results
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
