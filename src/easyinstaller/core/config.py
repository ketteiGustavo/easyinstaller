import json
import os
from pathlib import Path

# Define the XDG standard config directory for the application
CONFIG_DIR = Path.home() / '.config' / 'easyinstaller'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Define default paths using the standard user data location
DATA_DIR = Path.home() / '.local' / 'share' / 'easyinstaller'
DEFAULT_PATHS = {
    'export_dir': str(DATA_DIR / 'exports'),
    'history_file': str(DATA_DIR / 'history.jsonl'),
    'log_dir': str(DATA_DIR / 'logs'),
    'language': 'en_US',
}


def get_config() -> dict:
    """
    Loads the configuration from the JSON file.
    If the file or directory doesn't exist, it creates them with default values.
    """
    if not CONFIG_FILE.exists():
        return create_default_config()

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure all default keys are present
            for key, value in DEFAULT_PATHS.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, IOError):
        # If file is corrupted or unreadable, create a new default one
        return create_default_config()


def create_default_config() -> dict:
    """
    Creates the default configuration directory and file.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Create parent directories for default paths as well
        for path_str in DEFAULT_PATHS.values():
            Path(path_str).parent.mkdir(parents=True, exist_ok=True)

        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_PATHS, f, indent=2)
        return DEFAULT_PATHS
    except IOError:
        # If we can't write to the config file, return defaults in memory
        return DEFAULT_PATHS


def set_config_value(key: str, value: str):
    """
    Updates a specific configuration key with a new value and saves it.
    """
    current_config = get_config()
    current_config[key] = value
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=2)
        # Reload the global config object
        global config
        config = current_config
    except IOError as e:
        print(f'Error saving configuration: {e}')


# Load config once at import time
config = get_config()
