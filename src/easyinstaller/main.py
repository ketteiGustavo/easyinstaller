import typer

from easyinstaller.core.config import config
from easyinstaller.i18n.i18n import _, setup_i18n

setup_i18n(config['language'])

from easyinstaller.cli import add as add_app
from easyinstaller.cli import apt as apt_app
from easyinstaller.cli import completion as completion_app
from easyinstaller.cli import config as config_app
from easyinstaller.cli import export as export_app
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
app.add_typer(uninstall_app.app, name='uninstall')
app.add_typer(apt_app.app, name='apt')
app.add_typer(flatpak_app.app, name='fp')
app.add_typer(flatpak_app.app, name='flatpak')
app.add_typer(snap_app.app, name='snap')
app.add_typer(snap_app.app, name='sp')
app.add_typer(license_app.app, name='license')
app.add_typer(completion_app.app, name='completion')
app.add_typer(update_app.app, name='update')


@app.callback()
def main():
    """
    A universal installation manager for Linux.
    """
    pass


if __name__ == '__main__':
    app()
