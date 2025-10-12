import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager

console = Console()

app = typer.Typer(name='apt', help='Install a package using APT.')


@app.callback(invoke_without_command=True)
def apt(
    packages: list[str] = typer.Argument(
        ..., help='One or more APT packages to install.'
    )
):
    """
    Installs one or more packages using APT.
    """
    for package in packages:
        console.print(
            f'Adding [bold yellow]{package}[/bold yellow] via [bold green]APT[/bold green]...'
        )
        try:
            install_with_manager(package_name=package, manager='apt')
        except Exception as e:
            console.print(
                f'[red]An error occurred for package {package}:[/red] {e}'
            )
