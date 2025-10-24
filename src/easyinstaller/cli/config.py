from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from easyinstaller.core.config import get_config, set_config_value
from easyinstaller.i18n.i18n import _, setup_i18n

app = typer.Typer(
    name='config',
    help=_('Manages EasyInstaller configuration.'),
    invoke_without_command=True,
)
console = Console()

LANGUAGE_CHOICES = [
    ('en_US', 'English (United States)'),
    ('pt_BR', 'Português (Brasil)'),
]
LANGUAGE_CODES = {code for code, _ in LANGUAGE_CHOICES}
LANGUAGE_LABELS = {code: label for code, label in LANGUAGE_CHOICES}


@app.callback()
def show_config(ctx: typer.Context):
    """
    Shows the full configuration.
    """
    if ctx.invoked_subcommand:
        return

    cfg = get_config()

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


@app.command('get')
def get_config_value(
    key: str = typer.Argument(..., help=_('Configuration key to display.'))
):
    """
    Displays a single configuration value.
    """
    cfg = get_config()
    if key not in cfg:
        console.print(
            _(
                '[red]Error:[/red] Configuration key "[cyan]{key}[/cyan]" not found.'
            ).format(key=key)
        )
        raise typer.Exit(1)

    console.print(
        _('[cyan]{key}[/cyan]: {value}').format(key=key, value=cfg[key])
    )


@app.command('set')
def set_config(
    key: str = typer.Argument(..., help=_('Configuration key to update.')),
    value: str = typer.Argument(
        ..., help=_('New value to assign to the configuration key.')
    ),
):
    """
    Updates a configuration key with a new value.
    """
    set_config_value(key, value)
    console.print(
        _(
            '[bold green]Updated configuration:[/bold green] {key} = {value}'
        ).format(key=key, value=value)
    )


def _normalize_language_code(value: str) -> str:
    return value.replace('-', '_')


@app.command('language')
def configure_language(
    value: Optional[str] = typer.Argument(
        None,
        help=_('Optional language code to set without prompting.'),
    )
):
    """
    Interactively selects (or sets) the interface language.
    """
    cfg_value: Optional[str] = value

    if cfg_value is None:
        try:
            import questionary
        except ImportError:
            supported_codes = ', '.join(sorted(LANGUAGE_CODES))
            console.print(
                _(
                    '[red]Questionary is not installed.[/red] Install it with `pip install questionary` or run `ei config set language <code>` (codes: {codes}).'
                ).format(codes=supported_codes)
            )
            raise typer.Exit(1)

        choices = [
            questionary.Choice(
                title=f'{LANGUAGE_LABELS[code]} ({code})', value=code
            )
            for code, _ in LANGUAGE_CHOICES
        ]
        from easyinstaller.styles.styles import custom_style

        answer = questionary.select(
            _('Select the interface language:'),
            choices=choices,
            style=custom_style,
        ).ask()

        if answer is None:
            console.print(
                _(
                    '[yellow]No language selected. Configuration unchanged.[/yellow]'
                )
            )
            raise typer.Exit(0)

        cfg_value = answer

    normalized = _normalize_language_code(cfg_value)
    if normalized not in LANGUAGE_CODES:
        supported_codes = ', '.join(sorted(LANGUAGE_CODES))
        console.print(
            _(
                '[red]Error:[/red] Language "[yellow]{value}[/yellow]" is not supported. Available: {codes}'
            ).format(value=cfg_value, codes=supported_codes)
        )
        raise typer.Exit(1)

    set_config_value('language', normalized)
    setup_i18n(normalized)

    language_name = LANGUAGE_LABELS.get(normalized, normalized)
    console.print(
        _('[bold green]Language updated to[/bold green] {language}.').format(
            language=language_name
        )
    )
    console.print(
        _(
            '[blue]Reopen EasyInstaller commands to see every message in the selected language.[/blue]'
        )
    )
