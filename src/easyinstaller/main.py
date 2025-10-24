import sys
from pathlib import Path

import typer

from easyinstaller.core.config import config
from easyinstaller.i18n.i18n import _, setup_i18n
from easyinstaller.utils.update_prompt import UpdatePrompt

setup_i18n(config['language'])

from easyinstaller.cli import add as add_app
from easyinstaller.cli import apt as apt_app
from easyinstaller.cli import changelog as changelog_app
from easyinstaller.cli import completion as completion_app
from easyinstaller.cli import config as config_app
from easyinstaller.cli import export as export_app
from easyinstaller.cli import favorites as favorites_app
from easyinstaller.cli import flatpak as flatpak_app
from easyinstaller.cli import hist as hist_app
from easyinstaller.cli import import_app
from easyinstaller.cli import license as license_app
from easyinstaller.cli import list as list_app
from easyinstaller.cli import remove as rm_app
from easyinstaller.cli import snap as snap_app
from easyinstaller.cli import uninstall as uninstall_app
from easyinstaller.cli import update as update_app

app = typer.Typer(
    name='ei',
    help=_(
        '[bold green]EasyInstaller[/bold green]: A universal package manager for Linux, simplifying apt, flatpak, and snap.'
    ),
    add_completion=False,
    rich_markup_mode='rich',
    no_args_is_help=True,
)

app.add_typer(add_app.app, name='add')
app.add_typer(rm_app.app, name='rm')
app.add_typer(list_app.app, name='list')
app.add_typer(export_app.app, name='export')
app.add_typer(import_app.app, name='import')
app.add_typer(hist_app.app, name='hist')
app.add_typer(config_app.app, name='config')
app.add_typer(favorites_app.app, name='favorites')
app.add_typer(uninstall_app.app, name='uninstall')
app.add_typer(apt_app.app, name='apt')
app.add_typer(flatpak_app.app, name='flatpak')
app.add_typer(snap_app.app, name='snap')
app.add_typer(license_app.app, name='license')
app.add_typer(completion_app.app, name='completion')
app.add_typer(changelog_app.app, name='changelog')
app.add_typer(changelog_app.app, name='news')
app.add_typer(update_app.app, name='update')


ALIASES = {
    'fp': 'flatpak',
    'sp': 'snap',
}

_update_prompt = UpdatePrompt()


def _resolve_version() -> str:
    """Best-effort loader for the EasyInstaller version string."""
    # Candidate VERSION files when running from source or bundled binary
    possible_paths = [
        Path('/usr/local/share/easyinstaller') / 'VERSION',
        Path(__file__).resolve().parent / 'VERSION',
        Path(__file__).resolve().parent.parent / 'VERSION',
        Path(sys.executable).resolve().parent / 'easyinstaller' / 'VERSION',
        Path(sys.executable).resolve().parent / 'VERSION',
    ]

    for path in possible_paths:
        if path.is_file():
            try:
                return path.read_text(encoding='utf-8').strip()
            except OSError:
                continue

    return _('Unknown')


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        '--version',
        '-V',
        help=_('Show EasyInstaller version and exit.'),
    ),
):
    """A universal installation manager for Linux."""
    if version:
        typer.echo(_resolve_version())
        raise typer.Exit()

    _update_prompt.begin()

    # schedule update notification after the command finishes
    ctx.call_on_close(lambda: _update_prompt.notify(ctx))

    if ctx.invoked_subcommand is None and ctx.args:
        # no subcommand matched; Typer will handle
        return


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ALIASES:
        sys.argv[1] = ALIASES[sys.argv[1]]
    _update_prompt.begin()
    app()
