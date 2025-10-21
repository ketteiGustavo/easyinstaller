import json
import os

from easyinstaller.core.config import config


def get_history_file_path() -> str:
    """Ensures the history directory exists and returns the full path to the history file."""
    history_dir = os.path.expanduser('~/.local/share/easy-installer')
    os.makedirs(history_dir, exist_ok=True)
    return os.path.join(history_dir, 'history.jsonl')


def log_operation(operation_data: dict):
    """Appends a new operation record to the history file."""
    history_file = config['history_file']
    try:
        with open(history_file, 'a') as f:
            f.write(json.dumps(operation_data) + '\n')
    except IOError as e:
        # In a real CLI, you might want to handle this more gracefully
        print(f'Error writing to history file: {e}')
