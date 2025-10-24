from __future__ import annotations

from threading import Event, Thread
from typing import Optional

import typer
from rich.console import Console

from easyinstaller.core.versioning import (
    compare_versions,
    fetch_latest_release_info,
    get_installed_version,
)
from easyinstaller.i18n.i18n import _


class UpdatePrompt:
    """
    Background checker that quietly looks for new releases and,
    after the current command finishes, offers to run the updater.
    """

    def __init__(self, fetch_timeout: int = 5, wait_timeout: float = 0.5):
        self._fetch_timeout = fetch_timeout
        self._wait_timeout = wait_timeout
        self._event = Event()
        self._latest_version: Optional[str] = None
        self._thread: Optional[Thread] = None

    def begin(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        # Reset state for a fresh check each CLI execution
        self._event.clear()
        self._latest_version = None

        def worker() -> None:
            try:
                current = get_installed_version()
            except Exception:
                self._event.set()
                return

            try:
                release = fetch_latest_release_info(
                    timeout=self._fetch_timeout
                )
            except Exception:
                self._event.set()
                return

            latest_version = release.get('tag_name')
            if isinstance(latest_version, str) and compare_versions(
                current, latest_version
            ):
                self._latest_version = latest_version

            self._event.set()

        self._thread = Thread(target=worker, daemon=True)
        self._thread.start()

    def notify(self, ctx: typer.Context) -> None:
        if ctx.invoked_subcommand == 'update':
            return

        if not self._thread:
            return

        self._event.wait(timeout=self._wait_timeout)
        if not self._event.is_set():
            return

        if not self._latest_version:
            return

        console = Console()
        prompt = _(
            '[yellow]A newer version ({version}) is available. Do you want to update now?[/yellow]'
        ).format(version=self._latest_version)

        if not typer.confirm(prompt, default=False):
            console.print(
                _(
                    '[yellow]You can update later by running `ei update`.[/yellow]'
                )
            )
            return

        from easyinstaller.cli import (
            update as update_cli,
        )  # local import to avoid cycles

        console.print('[cyan]Running updater...[/cyan]')
        try:
            update_cli.update(auto_confirm=True)
        except typer.Exit:
            # update command uses typer.Exit to end execution; swallow it
            pass
