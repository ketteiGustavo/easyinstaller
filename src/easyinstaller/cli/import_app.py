import json

import typer
from rich import print

from easyinstaller.core.package_handler import (
    install_with_manager,
    prime_sudo_session,
)
from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='import',
    help=_('Installs packages from a previously exported JSON file.'),
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def import_packages(
    file_path: str = typer.Argument(
        ...,
        help=_(
            'Path to the JSON file containing the list of packages to install.'
        ),
    )
):
    """
    Import and install packages from a setup.json file.
    """
    print(
        _('Starting import from: [bold cyan]{file_path}[/bold cyan]').format(
            file_path=file_path
        )
    )

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            _(
                '[bold red]Error:[/bold red] File not found at [cyan]{file_path}[/cyan]'
            ).format(file_path=file_path)
        )
        raise typer.Exit(code=1)
    except json.JSONDecodeError:
        print(
            _(
                '[bold red]Error:[/bold red] Could not decode JSON from [cyan]{file_path}[/cyan]'
            ).format(file_path=file_path)
        )
        raise typer.Exit(code=1)

    packages_to_install = data.get('packages', {})
    if not packages_to_install:
        print(_('[yellow]No packages found in the file to install.[/yellow]'))
        return

    # Prime sudo session if apt or snap packages are present
    if any(
        manager in ('apt', 'snap') and packages
        for manager, packages in packages_to_install.items()
    ):
        prime_sudo_session()

    for manager, packages in packages_to_install.items():
        if packages:
            if manager == 'flatpak':
                package_ids = [pkg.get('id', pkg['name']) for pkg in packages]
            else:
                package_ids = [pkg['name'] for pkg in packages]

            print(
                _(
                    'Found {count} packages for [bold green]{manager}[/bold green].'
                ).format(count=len(package_ids), manager=manager)
            )

            # Confirm before installing
            if typer.confirm(
                _(
                    'Do you want to install these {count} packages using {manager}?'
                ).format(count=len(package_ids), manager=manager)
            ):
                print(
                    _('Installing packages with {manager}...').format(
                        manager=manager
                    )
                )
                try:
                    install_with_manager(package_ids, manager=manager)
                except SystemExit as e:
                    if e.code != 0:
                        print(
                            _(
                                '[bold red]Failed to install one or more packages ({manager}).[/bold red]'
                            ).format(manager=manager)
                        )
                        continue
                print(
                    _(
                        '[bold green]✔ Installation process for {manager} complete.[/bold green]'
                    ).format(manager=manager)
                )
            else:
                print(
                    _('Skipping installation for {manager} packages.').format(
                        manager=manager
                    )
                )

    print(_('[bold green]✔ Import process finished![/bold green]'))
