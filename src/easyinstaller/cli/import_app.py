import json

import typer
from rich import print

from easyinstaller.core.package_handler import install_with_manager

app = typer.Typer()


@app.callback(invoke_without_command=True)
def import_packages(
    file_path: str = typer.Argument(
        ..., help='Path to the setup.json file to import packages from.'
    )
):
    """
    Import and install packages from a setup.json file.
    """
    print(f'Starting import from: [bold cyan]{file_path}[/bold cyan]')

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f'[bold red]Error:[/bold red] File not found at [cyan]{file_path}[/cyan]'
        )
        raise typer.Exit(code=1)
    except json.JSONDecodeError:
        print(
            f'[bold red]Error:[/bold red] Could not decode JSON from [cyan]{file_path}[/cyan]'
        )
        raise typer.Exit(code=1)

    packages_to_install = data.get('packages', {})
    if not packages_to_install:
        print('[yellow]No packages found in the file to install.[/yellow]')
        return

    for manager, packages in packages_to_install.items():
        if packages:
            if manager == 'flatpak':
                package_ids = [pkg.get('id', pkg['name']) for pkg in packages]
            else:
                package_ids = [pkg['name'] for pkg in packages]

            print(
                f'Found {len(package_ids)} packages for [bold green]{manager}[/bold green].'
            )

            # Confirm before installing
            if typer.confirm(
                f'Do you want to install these {len(package_ids)} packages using {manager}?'
            ):
                print(f'Installing packages with {manager}...')
                for package_id in package_ids:
                    try:
                        install_with_manager(package_id, manager=manager)
                    except SystemExit as e:
                        if e.code != 0:
                            print(
                                f'[bold red]Failed to install {package_id}. Continuing with next package...[/bold red]'
                            )
                print(
                    f'[bold green]✔ Installation process for {manager} complete.[/bold green]'
                )
            else:
                print(f'Skipping installation for {manager} packages.')

    print('[bold green]✔ Import process finished![/bold green]')


if __name__ == '__main__':
    app()
