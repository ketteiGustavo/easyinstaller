import typer
from rich.console import Console

from easyinstaller.cli.utils.ask import ask_user_to_select_packages
from easyinstaller.core.package_handler import (
    install_with_manager,
    prime_sudo_session,
)
from easyinstaller.core.searcher import unified_search
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='add',
    help=_('Searches for and installs packages from apt, flatpak, and snap.'),
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def add(
    packages: list[str] = typer.Argument(
        ..., help=_('One or more packages to search for and install.')
    )
):
    """
    Finds and installs one or more packages from any available source.
    """
    packages_to_install = []
    for package_query in packages:
        console.print(
            _(
                "---\n[bold]Searching for [yellow]'{package_query}'[/yellow]...[/bold]"
            ).format(package_query=package_query)
        )
        results = unified_search(package_query)

        if not results:
            console.print(
                _(
                    "No results found for [yellow]'{package_query}'[/yellow]."
                ).format(package_query=package_query)
            )
            continue

        selected_packages = []
        # If there is only one result and its name is an exact match, select it automatically.
        if (
            len(results) == 1
            and results[0]['name'].lower() == package_query.lower()
        ):
            package = results[0]
            console.print(
                _(
                    'Found one exact match: [green]{name}[/green] ([cyan]{source}[/cyan]). Installing automatically.'
                ).format(name=package['name'], source=package['source'])
            )
            selected_packages = [package]
        else:
            # Otherwise, ask the user to select from the list of results.
            user_selection = ask_user_to_select_packages(results)
            if user_selection:
                selected_packages = user_selection

        if selected_packages:
            packages_to_install.extend(selected_packages)

    if packages_to_install:
        # Prime sudo session if apt or snap packages are present
        if any(p['source'] in ('apt', 'snap') for p in packages_to_install):
            prime_sudo_session()

        for package in packages_to_install:
            console.print(
                _(
                    'Installing [green]{name}[/green] from [cyan]{source}[/cyan]...'
                ).format(name=package['name'], source=package['source'])
            )
            try:
                install_with_manager(
                    package_names=package['id'], manager=package['source']
                )
            except Exception as e:
                console.print(
                    _(
                        '[red]An error occurred while installing {name}:[/red] {error}'
                    ).format(name=package['name'], error=e)
                )
