import typer
from rich.console import Console

from easyinstaller.core.searcher import unified_search
from easyinstaller.core.package_handler import install_with_manager
from easyinstaller.cli.utils.ask import ask_user_to_select_package

console = Console()

app = typer.Typer(
    name="add",
    help="Find and install a package from any available source (apt, flatpak, snap).",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def add(packages: list[str] = typer.Argument(..., help="One or more packages to search for and install.")):
    """
    Finds and installs one or more packages from any available source.
    """
    for package_query in packages:
        console.print(f"---\n[bold]Searching for [yellow]'{package_query}'[/yellow]...[/bold]")
        results = unified_search(package_query)

        if not results:
            console.print(f"No results found for [yellow]'{package_query}'[/yellow].")
            continue

        selected_package = None
        if len(results) == 1:
            selected_package = results[0]
            console.print(f"Found one match: [green]{selected_package['name']}[/green] ([cyan]{selected_package['source']}[/cyan]). Installing automatically.")
        else:
            selected_package = ask_user_to_select_package(results)

        if selected_package:
            console.print(f"Installing [green]{selected_package['name']}[/green] from [cyan]{selected_package['source']}[/cyan]...")
            try:
                install_with_manager(package_name=selected_package['id'], manager=selected_package['source'])
            except Exception as e:
                console.print(f"[red]An error occurred while installing {selected_package['name']}:[/red] {e}")


