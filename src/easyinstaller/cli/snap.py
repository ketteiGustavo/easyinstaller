import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager

console = Console()

app = typer.Typer(name='snap', help='Install a package using Snap.')


@app.callback(invoke_without_command=True)
def snap(
    packages: list[str] = typer.Argument(
        ..., help='One or more Snap packages to install.'
    )
):
    """
    Installs one or more packages using Snap.
    """
    for package in packages:
        console.print(
            f'Adding [bold yellow]{package}[/bold yellow] via [bold green]Snap[/bold green]...'
        )
        try:
            install_with_manager(package_name=package, manager='snap')
        except Exception as e:
            console.print(
                f'[red]An error occurred for package {package}:[/red] {e}'
            )
