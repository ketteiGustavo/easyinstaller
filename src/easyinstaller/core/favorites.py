from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from easyinstaller.core.config import CONFIG_DIR

FAVORITES_FILE = CONFIG_DIR / 'favorites.json'
DEFAULT_FAVORITES: Dict[str, List[Dict]] = {
    'apt': [],
    'flatpak': [],
    'snap': [],
}


def load_favorites() -> Dict[str, List[Dict]]:
    if not FAVORITES_FILE.exists():
        return {manager: items[:] for manager, items in DEFAULT_FAVORITES.items()}
    try:
        data = json.loads(FAVORITES_FILE.read_text(encoding='utf-8'))
        favorites: Dict[str, List[Dict]] = {
            manager: data.get(manager, []) for manager in DEFAULT_FAVORITES
        }
        return favorites
    except (json.JSONDecodeError, OSError):
        return {manager: items[:] for manager, items in DEFAULT_FAVORITES.items()}


def save_favorites(favorites: Dict[str, List[Dict]]) -> None:
    FAVORITES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {manager: favorites.get(manager, []) for manager in DEFAULT_FAVORITES}
    FAVORITES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def clear_favorites() -> None:
    save_favorites(DEFAULT_FAVORITES)


def favorites_count(favorites: Dict[str, List[Dict]]) -> int:
    return sum(len(items) for items in favorites.values())


def is_favorite(pkg: Dict, favorites: Dict[str, List[Dict]]) -> bool:
    manager = pkg.get('source')
    name = pkg.get('name')
    if not manager or not name:
        return False
    for entry in favorites.get(manager, []):
        if entry.get('name') == name:
            return True
    return False
