import typer
from rich.console import Console
from rich.table import Table

from easyinstaller.core.lister import unified_lister

console = Console()

app = typer.Typer(
    name='list',
    help='List installed packages, optionally filtering by manager (apt, flatpak, snap).',
)


@app.callback(invoke_without_command=True)
def list_packages(
    managers: list[str] = typer.Argument(
        None,
        help='Optional: Specify one or more managers to list (e.g., apt, snap).',
    )
):
    """
    Lists installed packages from specified managers, or all if none are specified.
    """
    # If no managers are specified, default to all
    if not managers:
        managers = None   # unified_lister handles None as 'all'

    title = 'Installed Packages'
    if managers:
        title = f"Installed Packages ({ ', '.join(managers) })"

    with console.status(
        '[bold green]Fetching installed packages...[/bold green]'
    ):
        packages = unified_lister(managers)

    if not packages:
        console.print(
            '[yellow]No packages found for the specified managers.[/yellow]'
        )
        return

    table = Table(title=title)
    table.add_column('Package Name', style='cyan', no_wrap=True)
    table.add_column('Version', style='magenta')
    table.add_column('Size', style='green')
    table.add_column('Source', style='yellow')

    # Group packages by source for organized display
    grouped_packages = {}
    for pkg in packages:
        source = pkg['source']
        if source not in grouped_packages:
            grouped_packages[source] = []
        grouped_packages[source].append(pkg)

    # Use the provided manager order if available, otherwise sort alphabetically
    source_order = managers if managers else sorted(grouped_packages.keys())

    for source in source_order:
        if source in grouped_packages:
            table.add_section()
            for pkg in sorted(
                grouped_packages[source], key=lambda i: i['name']
            ):
                table.add_row(
                    pkg['name'], pkg['version'], pkg['size'], pkg['source']
                )

    console.print(table)
