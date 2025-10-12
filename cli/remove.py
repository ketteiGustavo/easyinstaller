import typer
from rich.console import Console

from easyinstaller.core.package_handler import remove_package

console = Console()

app = typer.Typer(
    name="rm",
    help="Remove a package using a specific package manager.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def rm(manager: str = typer.Argument(..., help="The package manager to use (e.g., apt, flatpak, snap)."),
       package: str = typer.Argument(..., help="The name of the package to remove.")):
    """
    Removes a package using the specified package manager.
    """
    console.print(f"Removing [bold yellow]{package}[/bold yellow] via [bold green]{manager}[/bold green]...")
    try:
        remove_package(package_name=package, manager_type=manager)
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
        raise typer.Exit(1)
