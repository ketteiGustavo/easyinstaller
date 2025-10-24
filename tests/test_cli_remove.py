from typer.testing import CliRunner

from easyinstaller.cli import remove as remove_module


def test_rm_accepts_flatpak_id(monkeypatch):
    runner = CliRunner()

    def fake_unified_lister():
        return [
            {
                'name': 'Mission Center',
                'id': 'io.missioncenter.MissionCenter',
                'source': 'flatpak',
                'version': '1.0',
                'size': '10 MB',
            }
        ]

    recorded_calls = []

    def fake_remove_with_manager(package_name, manager, purge):
        recorded_calls.append((package_name, manager, purge))

    monkeypatch.setattr(remove_module, 'unified_lister', fake_unified_lister)
    monkeypatch.setattr(
        remove_module, 'remove_with_manager', fake_remove_with_manager
    )

    result = runner.invoke(
        remove_module.app, ['io.missioncenter.MissionCenter', '--yes']
    )

    assert result.exit_code == 0
    assert recorded_calls == [
        ('io.missioncenter.MissionCenter', 'flatpak', False)
    ]
