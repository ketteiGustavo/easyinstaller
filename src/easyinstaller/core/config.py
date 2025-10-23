import json
import os
from pathlib import Path

from easyinstaller.i18n.i18n import _

# Define the XDG standard config directory for the application
CONFIG_DIR = Path.home() / '.config' / 'easyinstaller'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Define default paths using the standard user data location
DATA_DIR = Path.home() / '.local' / 'share' / 'easyinstaller'
EXPORT_DIR = DATA_DIR / 'exports'
LOG_DIR = DATA_DIR / 'logs'
HIST_FILE = DATA_DIR / 'history.jsonl'


def default_paths() -> dict:
    """
    Returns a dictionary of default paths for configuration.
    """
    return {
        'export_path': str(EXPORT_DIR),
        'log_path': str(LOG_DIR),
        'history_file': str(HIST_FILE),
        'language': 'en_US',
    }


def _ensure_dirs(cfg: dict) -> None:
    """
    Ensures that the necessary directories exist.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in [EXPORT_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    Path(cfg['history_file']).parent.mkdir(parents=True, exist_ok=True)


def create_default_config() -> dict:
    """
    Creates the default configuration directory and file.
    """
    cfg = default_paths()
    _ensure_dirs(cfg)

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
    except IOError as e:
        # If we can't write to the config file, return defaults in memory
        print(_(f'Warning: could not write config file: {e}'))

    return cfg


def get_config() -> dict:
    """
    Loads the configuration from the JSON file.
    If the file or directory doesn't exist, it creates them with default values.
    """
    if not CONFIG_FILE.exists():
        return create_default_config()
    else:
        try:
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or unreadable, create a new default one
            cfg = create_default_config()

        for key, value in default_paths().items():
            cfg.setdefault(key, value)

        _ensure_dirs(cfg)
    return cfg


def set_config_value(key: str, value: str):
    """
    Updates a specific configuration key with a new value and saves it.
    """
    cfg = get_config()
    cfg[key] = value
    try:
        _ensure_dirs(cfg)
    except IOError as e:
        print(_(f'Error saving configuration: {e}'))
        pass

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
        global config
        config = cfg
    except IOError as e:
        print(_(f'Error saving configuration: {e}'))


# Load config once at import time
config = get_config()
