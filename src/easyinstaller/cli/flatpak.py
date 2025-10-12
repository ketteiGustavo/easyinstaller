import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager

console = Console()

app = typer.Typer(
    name='flatpak',
    help='Install a package using Flatpak.',
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def flatpak(
    packages: list[str] = typer.Argument(
        ..., help='One or more Flatpak packages to install.'
    )
):
    """
    Installs one or more packages using Flatpak.
    """
    for package in packages:
        console.print(
            f'Adding [bold yellow]{package}[/bold yellow] via [bold green]Flatpak[/bold green]...'
        )
        try:
            # This is where the search logic will go
            install_with_manager(package_name=package, manager='flatpak')
        except Exception as e:
            console.print(
                f'[red]An error occurred for package {package}:[/red] {e}'
            )
