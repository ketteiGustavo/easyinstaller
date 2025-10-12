import typer
from rich.console import Console

from easyinstaller.cli.utils.ask import ask_user_to_select_packages
from easyinstaller.core.package_handler import remove_with_manager
from easyinstaller.core.searcher import unified_search

console = Console()

app = typer.Typer(
    name='rm',
    help='Find and remove a package from any available source (apt, flatpak, snap).',
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def rm(
    packages: list[str] = typer.Argument(
        ..., help='One or more packages to search for and remove.'
    ),
    purge: bool = typer.Option(
        False,
        '--purge',
        help='Use "purge" instead of "remove" for apt (removes configuration files).',
    ),
):
    """
    Finds and removes one or more packages from any available source.
    """
    for package_query in packages:
        console.print(
            f"---\n[bold]Searching for [yellow]'{package_query}'[/yellow] to remove...[/bold]"
        )
        results = unified_search(package_query)

        if not results:
            console.print(
                f"No installed packages found matching [yellow]'{package_query}'[/yellow]."
            )
            continue

        selected_packages = ask_user_to_select_packages(results)

        if selected_packages:
            for package in selected_packages:
                console.print(
                    f"Removing [green]{package['name']}[/green] from [cyan]{package['source']}[/cyan]..."
                )
                try:
                    remove_with_manager(
                        package_name=package['id'],
                        manager=package['source'],
                        purge=purge,
                    )
                except Exception as e:
                    console.print(
                        f"[red]An error occurred while removing {package['name']}:[/red] {e}"
                    )
