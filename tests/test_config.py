from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def reload_config(tmp_path, monkeypatch):
    """
    Reloads the configuration module using a temporary HOME directory so we can
    test migrations without touching the real user config.
    """
    home_dir = tmp_path / 'home'
    home_dir.mkdir()
    monkeypatch.setenv('HOME', str(home_dir))

    from easyinstaller.core import config as config_mod

    reloaded = importlib.reload(config_mod)
    yield reloaded

    importlib.reload(config_mod)


def test_get_config_persists_aliases(reload_config):
    config_mod = reload_config

    cfg = config_mod.get_config()

    assert cfg['log_dir'] == cfg['log_path']
    assert cfg['export_dir'] == cfg['export_path']

    with open(config_mod.CONFIG_FILE, 'r', encoding='utf-8') as fh:
        stored = json.load(fh)

    assert stored['log_dir'] == cfg['log_path']
    assert stored['export_dir'] == cfg['export_path']
