import typer
from rich.console import Console

from easyinstaller.core.package_handler import remove_package

console = Console()

app = typer.Typer(
    name='rm',
    help='Remove a package using a specific package manager.',
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def rm(
    packages: list[str] = typer.Argument(
        ..., help='One or more packages to remove.'
    )
):
    """
    Removes one or more packages using the system's native package manager.
    """
    for package in packages:
        console.print(
            f'Removing [bold yellow]{package}[/bold yellow] using native package manager...'
        )
        try:
            remove_package(package_name=package)
        except Exception as e:
            console.print(
                f'[red]An error occurred for package {package}:[/red] {e}'
            )
