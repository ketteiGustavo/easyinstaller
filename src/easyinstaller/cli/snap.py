import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(name='snap', help=_('Install a package using Snap.'))


@app.callback(invoke_without_command=True)
def snap(
    packages: list[str] = typer.Argument(
        ..., help=_('One or more Snap packages to install.')
    )
):
    """
    Installs one or more packages using Snap.
    """
    for package in packages:
        console.print(
            _(
                'Adding [bold yellow]{package}[/bold yellow] via [bold green]Snap[/bold green]...'
            ).format(package=package)
        )
        try:
            install_with_manager(package_names=package, manager='snap')
        except Exception as e:
            console.print(
                _(
                    '[red]An error occurred for package {package}:[/red] {error}'
                ).format(package=package, error=e)
            )
