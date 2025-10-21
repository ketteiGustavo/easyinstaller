from unittest.mock import MagicMock, patch

import easyinstaller.core.runner as runner


def test_run_cmd_smart_fallbacks_to_subprocess_with_env_merge():
    subprocess_result = MagicMock(returncode=3)

    with patch('easyinstaller.core.runner.HAS_PEXPECT', False), patch(
        'easyinstaller.core.runner.subprocess.run',
        return_value=subprocess_result,
    ) as run_mock, patch.object(runner.console, 'status') as status_mock:
        status_mock.return_value.__enter__.return_value = None
        status_mock.return_value.__exit__.return_value = None

        rc = runner.run_cmd_smart('echo hi', env={'FOO': 'BAR'})

    assert rc == 3
    run_mock.assert_called_once()
    args, kwargs = run_mock.call_args
    assert args[0] == ['echo', 'hi']
    assert kwargs['env']['FOO'] == 'BAR'
    # The merged environment should still include the existing PATH variable.
    assert 'PATH' in kwargs['env']
