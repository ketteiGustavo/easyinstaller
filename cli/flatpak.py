import typer
from rich.console import Console

from easyinstaller.core.package_handler import install_with_manager

console = Console()

app = typer.Typer(
    name="flatpak",
    help="Install a package using Flatpak.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def flatpak(package: str = typer.Argument(..., help="The name of the Flatpak package to install (e.g., com.spotify.Client).")):
    """
    Installs a package using Flatpak.
    """
    console.print(f"Adding [bold yellow]{package}[/bold yellow] via [bold green]Flatpak[/bold green]...")
    try:
        install_with_manager(package_name=package, manager="flatpak")
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
        raise typer.Exit(1)
