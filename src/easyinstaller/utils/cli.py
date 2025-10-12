import subprocess
import sys


def _run(cmd: list[str]) -> int:
    print('$', ' '.join(cmd))
    return subprocess.call(cmd)


def format() -> None:
    """Aplica isort e blue no projeto."""
    cmds = [
        ['isort', 'src/', 'tests/'],
        ['blue', 'src/', 'tests/'],
    ]
    for cmd in cmds:
        rc = _run(cmd)
        if rc != 0:
            sys.exit(rc)


def lint() -> None:
    """Checa sem modificar arquivos."""
    cmds = [
        ['isort', 'src/', 'tests/', '--check-only', '--diff'],
        ['blue', 'src/', 'tests/', '--check'],
    ]
    for cmd in cmds:
        rc = _run(cmd)
        if rc != 0:
            sys.exit(rc)
