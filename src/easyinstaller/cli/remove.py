import typer
from rich.console import Console

from easyinstaller.cli.utils.ask import ask_user_to_select_packages
from easyinstaller.core.lister import unified_lister
from easyinstaller.core.package_handler import remove_with_manager
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='rm',
    help=_('Finds and removes an installed package by its exact name.'),
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def rm(
    packages_and_flags: list[str] = typer.Argument(
        ..., help=_('One or more installed packages to remove.')
    ),
    purge: bool = typer.Option(
        False,
        '--purge',
        help=_(
            "Use 'purge' instead of 'remove' for apt (removes configuration files)."
        ),
    ),
    yes: bool = typer.Option(
        False,
        '--yes',
        '-y',
        help=_('Automatically answer "yes" to confirmation prompts.'),
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
        console.print(_('[red]Error:[/red] No package names provided.'))
        raise typer.Exit(code=1)

    console.print(_('[cyan]Fetching installed packages...[/cyan]'))
    installed_packages = unified_lister()

    if not installed_packages:
        console.print(
            _('[yellow]No installed packages found on the system.[/yellow]')
        )
        return

    for package_query in packages_to_remove:
        console.print(
            _(
                "---\n[bold]Searching for exact match for [yellow]'{package_query}'[/yellow]...[/bold]"
            ).format(package_query=package_query)
        )

        normalized_query = package_query.lower()
        exact_matches = [
            pkg
            for pkg in installed_packages
            if any(
                normalized_query == candidate.lower()
                for candidate in (
                    pkg.get('name', ''),
                    pkg.get('id', ''),
                )
                if candidate
            )
        ]

        packages_to_process = []

        if len(exact_matches) == 1:
            package = exact_matches[0]
            if auto_confirm or typer.confirm(
                _(
                    'Found installed package: {name} [{source}]\nRemove it?'
                ).format(name=package['name'], source=package['source'])
            ):
                packages_to_process.append(package)

        elif len(exact_matches) > 1:
            if auto_confirm:
                console.print(
                    _(
                        "[red]Error:[/red] Multiple packages named '[yellow]{package_query}[/yellow]' found. "
                        "Cannot use '-y' in an ambiguous situation. Please run without '-y' and select manually."
                    ).format(package_query=package_query)
                )
                continue

            console.print(
                _(
                    "Found multiple packages with the name [yellow]'{package_query}'[/yellow]'. Please choose which to remove."
                ).format(package_query=package_query)
            )
            selected = ask_user_to_select_packages(exact_matches)
            if selected:
                packages_to_process.extend(selected)
        else:
            console.print(
                _(
                    "[red]Error:[/red] Unable to locate an installed package named [yellow]'{package_query}'[/yellow].."
                ).format(package_query=package_query)
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
                        _(
                            '[red]Could not determine package identifier for {package}. Skipping.[/red]'
                        ).format(package=package)
                    )
                    continue

                console.print(
                    _(
                        'Removing [green]{name}[/green] ([cyan]{package_id}[/cyan]) from [cyan]{source}[/cyan]...'
                    ).format(
                        name=package['name'],
                        package_id=package_id,
                        source=package['source'],
                    )
                )
                try:
                    remove_with_manager(
                        package_name=package_id,
                        manager=package.get('source'),
                        purge=purge,
                    )
                except Exception as e:
                    console.print(
                        _(
                            '[red]An error occurred while removing {name}:[/red] {error}'
                        ).format(name=package['name'], error=e)
                    )
