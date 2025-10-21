import typer
from rich.console import Console

from easyinstaller.cli.utils.ask import ask_user_to_select_packages
from easyinstaller.core.lister import unified_lister
from easyinstaller.core.package_handler import remove_with_manager

console = Console()

app = typer.Typer(
    name='rm',
    help='Finds and removes an installed package by its exact name.',
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def rm(
    packages_and_flags: list[str] = typer.Argument(
        ..., help='One or more installed packages to remove.'
    ),
    purge: bool = typer.Option(
        False,
        '--purge',
        help="Use 'purge' instead of 'remove' for apt (removes configuration files).",
    ),
    yes: bool = typer.Option(
        False,
        '--yes',
        '-y',
        help='Automatically answer "yes" to confirmation prompts.',
        is_flag=True,  # Keep for documentation purposes
    ),
):
    """
    Finds and removes one or more installed packages.
    """
    # --- Manual parsing to handle typer's greedy list argument ---
    packages_to_remove = []
    auto_confirm = yes  # Start with the value from typer's parsing
    for item in packages_and_flags:
        if item in ('-y', '--yes'):
            auto_confirm = True
        else:
            packages_to_remove.append(item)
    # --- End of manual parsing ---

    if not packages_to_remove:
        console.print('[red]Error:[/red] No package names provided.')
        raise typer.Exit(code=1)

    console.print('[cyan]Fetching installed packages...[/cyan]')
    installed_packages = unified_lister()

    if not installed_packages:
        console.print(
            '[yellow]No installed packages found on the system.[/yellow]'
        )
        return

    for package_query in packages_to_remove:
        console.print(
            f"---\n[bold]Searching for exact match for [yellow]'{package_query}'[/yellow]...[/bold]"
        )

        exact_matches = [
            pkg
            for pkg in installed_packages
            if package_query.lower() == pkg.get('name', '').lower()
        ]

        packages_to_process = []

        if len(exact_matches) == 1:
            package = exact_matches[0]
            if auto_confirm or typer.confirm(
                f"Found installed package: {package['name']} [{package['source']}]\nRemove it?"
            ):
                packages_to_process.append(package)

        elif len(exact_matches) > 1:
            if auto_confirm:
                console.print(
                    f"[red]Error:[/red] Multiple packages named '[yellow]{package_query}[/yellow]' found. "
                    f"Cannot use '-y' in an ambiguous situation. Please run without '-y' and select manually."
                )
                continue

            console.print(
                f"Found multiple packages with the name [yellow]'{package_query}'[/yellow]'. Please choose which to remove."
            )
            selected = ask_user_to_select_packages(exact_matches)
            if selected:
                packages_to_process.extend(selected)
        else:
            console.print(
                f"[red]Error:[/red] Unable to locate an installed package named [yellow]'{package_query}'[/yellow].."
            )
            continue

        if packages_to_process:
            for package in packages_to_process:
                package_id = (
                    package.get('id')
                    if package.get('source') == 'flatpak'
                    else package.get('name')
                )

                if not package_id:
                    console.print(
                        f'[red]Could not determine package identifier for {package}. Skipping.[/red]'
                    )
                    continue

                console.print(
                    f"Removing [green]{package['name']}[/green] ([cyan]{package_id}[/cyan]) from [cyan]{package['source']}[/cyan]..."
                )
                try:
                    remove_with_manager(
                        package_name=package_id,
                        manager=package.get('source'),
                        purge=purge,
                    )
                except Exception as e:
                    console.print(
                        f"[red]An error occurred while removing {package['name']}:[/red] {e}"
                    )
