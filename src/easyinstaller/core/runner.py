from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import threading
import time
from typing import Callable, Optional

try:
    import pexpect  # type: ignore

    HAS_PEXPECT = True
except ImportError:
    HAS_PEXPECT = False

from rich.console import Console

from easyinstaller.i18n.i18n import _

console = Console()

PROMPTS = re.compile(
    r'(?i)(do you want to continue\?|'
    r'[y/n]|[y/N]|(y/n)|'
    r'eula|license|terms|'
    r'configuring\s+|press enter|password:|'
    r'gpg|signature|import key|permissions)'
)


def _spinner(stop_event, label=_('Installing...')):
    frames = '|/-\\'
    i = 0
    while not stop_event.is_set():
        console.print(f'\r{label} {frames[i % len(frames)]}', end='')
        i += 1
        time.sleep(0.1)
    console.print('\r' + ' ' * (len(label) + 2) + '\r', end='')


def run_cmd_smart(
    cmd: str, env: Optional[dict] = None, log_path: Optional[str] = None
) -> int:
    """
    Executes a command with a spinner and prompt detection.
    If interaction is detected, it pauses the spinner and hands over the TTY to the user.
    Requires pexpect for the full experience; otherwise, it falls back to subprocess.
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    if not HAS_PEXPECT:
        # Fallback without prompt detection
        with console.status(
            _('[bold cyan]Running (no pexpect):[/] {cmd}').format(cmd=cmd)
        ):
            proc = subprocess.run(shlex.split(cmd), env=merged_env)
            return proc.returncode

    child = pexpect.spawn(
        '/bin/bash',
        ['-c', cmd],
        env=merged_env,
        encoding='utf-8',
        timeout=None,
    )
    stop = threading.Event()
    spin = threading.Thread(
        target=_spinner,
        args=(
            stop,
            _('Running: {cmd_name}...').format(cmd_name=cmd.split()[0]),
        ),
    )
    spin.start()

    log_fh = open(log_path, 'a', encoding='utf-8') if log_path else None
    buffer = ''
    exit_status = 0

    try:
        while True:
            try:
                chunk = child.read_nonblocking(size=1024, timeout=5)
                if not chunk:
                    continue
                buffer += chunk
                if log_fh:
                    log_fh.write(chunk)
                    log_fh.flush()

                if PROMPTS.search(buffer):
                    stop.set()
                    spin.join()
                    sys.stdout.write(buffer)
                    sys.stdout.flush()
                    buffer = ''
                    child.interact()  # User takes over
                    break
            except pexpect.exceptions.TIMEOUT:
                pass   # Temporary silence is fine, keep the spinner going
            except pexpect.exceptions.EOF:
                break
    finally:
        stop.set()
        if spin.is_alive():
            spin.join()
        if log_fh:
            log_fh.close()

        # Ensure the child process has terminated
        if child.isalive():
            child.wait()

        exit_status = (
            child.exitstatus
            if child.exitstatus is not None
            else child.signalstatus or 1
        )

    return exit_status
