from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from easyinstaller.core.config import get_config, set_config_value
from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='config',
    help=_('Manages EasyInstaller configuration.'),
    invoke_without_command=True,
)
console = Console()


@app.callback()
def show_config(
    key: Optional[str] = typer.Argument(
        None, help=_('Optional configuration key to display.')
    )
):
    """
    Shows the configuration or a specific key.
    """
    cfg = get_config()

    if key:
        if key not in cfg:
            console.print(
                _(
                    '[red]Error:[/red] Configuration key "[cyan]{key}[/cyan]" not found.'
                ).format(key=key)
            )
            raise typer.Exit(1)

        console.print(f'[cyan]{key}[/cyan]: {cfg[key]}')
        return

    table = Table(
        title=_('Configuration'),
        show_header=True,
        header_style='bold magenta',
    )
    table.add_column(_('Key'), style='cyan')
    table.add_column(_('Value'), overflow='fold')

    for cfg_key in sorted(cfg):
        table.add_row(cfg_key, str(cfg[cfg_key]))

    console.print(table)


@app.command('set')
def set_config(
    key: str = typer.Argument(
        ..., help=_('Configuration key to update.')
    ),
    value: str = typer.Argument(
        ..., help=_('New value to assign to the configuration key.')
    ),
):
    """
    Updates a configuration key with a new value.
    """
    set_config_value(key, value)
    console.print(
        _('[bold green]Updated configuration:[/bold green] {key} = {value}').format(
            key=key, value=value
        )
    )
