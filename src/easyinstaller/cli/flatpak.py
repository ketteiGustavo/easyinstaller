import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='flatpak',
    help=_('Install a package using Flatpak.'),
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def flatpak(
    packages: list[str] = typer.Argument(
        ..., help=_('One or more Flatpak packages to install.')
    )
):
    """
    Installs one or more packages using Flatpak.
    """
    for package in packages:
        console.print(
            _(
                'Adding [bold yellow]{package}[/bold yellow] via [bold green]Flatpak[/bold green]...'
            ).format(package=package)
        )
        try:
            # This is where the search logic will go
            install_with_manager(package_names=package, manager='flatpak')
        except Exception as e:
            console.print(
                _(
                    '[red]An error occurred for package {package}:[/red] {error}'
                ).format(package=package, error=e)
            )
