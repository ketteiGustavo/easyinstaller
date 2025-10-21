import os

import typer
from rich.console import Console

from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='license',
    help=_('Displays the easyinstaller license information.'),
    no_args_is_help=True,
)
console = Console()

# Define the standard user data location where the license file will be stored
DATA_DIR = '/usr/local/share/easyinstaller'
LICENSE_PATH = os.path.join(DATA_DIR, 'LICENSE')


@app.callback(invoke_without_command=True)
def show_license():
    """
    Displays the easyinstaller license information.
    """
    if not os.path.exists(LICENSE_PATH):
        console.print(
            _(
                '[red]Error:[/red] License file not found at [cyan]{path}[/cyan].'
            ).format(path=LICENSE_PATH)
        )
        console.print(
            _(
                'Please ensure easyinstaller was installed correctly or run `ei update`.'
            )
        )
        raise typer.Exit(1)

    try:
        with open(LICENSE_PATH, 'r') as f:
            license_content = f.read()
        console.print(license_content)
    except IOError as e:
        console.print(
            _('[red]Error reading license file:[/red] {error}').format(error=e)
        )
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
