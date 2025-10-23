from __future__ import annotations

import sys
from typing import Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

from easyinstaller.core.favorites import (
    clear_favorites,
    favorites_count,
    is_favorite,
    load_favorites,
    save_favorites,
)
from easyinstaller.core.lister import unified_lister
from easyinstaller.core.package_filters import (
    DEFAULT_MANAGERS,
    filter_user_app_packages,
    group_packages_by_manager,
)
from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='favorites',
    help=_('Manage and export your favorite applications.'),
    invoke_without_command=True,
)

VALID_MANAGERS = {manager for manager in DEFAULT_MANAGERS}


def _require_questionary():
    try:
        import questionary  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime dependency
        console.print(
            _(
                '[red]Questionary is required for interactive selection.[/red] Install it with `pip install questionary` and retry.'
            )
        )
        raise typer.Exit(1) from exc

    if not sys.stdin.isatty():  # pragma: no cover - environment dependent
        console.print(
            _(
                '[red]Interactive selection requires a TTY.[/red] Run this command directly in a terminal.'
            )
        )
        raise typer.Exit(1)

    return questionary


def _choice_title(pkg: Dict) -> str:
    manager = pkg.get('source', '').upper()
    name = pkg.get('name', '')
    version = pkg.get('version') or ''
    if version:
        return f'[{manager}] {name} ({version})'
    return f'[{manager}] {name}'


def _package_key(pkg: Dict) -> Tuple[str, str]:
    return (pkg.get('source', ''), pkg.get('name', ''))


def _build_favorites_payload(packages: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = group_packages_by_manager(packages, DEFAULT_MANAGERS)
    favorites: Dict[str, List[Dict]] = {}
    for manager, entries in grouped.items():
        favorites[manager] = [
            {
                'name': entry.get('name'),
                'version': entry.get('version'),
                'size': entry.get('size'),
                'id': entry.get('id'),
            }
            for entry in entries
        ]
    return favorites


def _normalize_manager_options(
    managers: Optional[List[str]],
) -> List[str]:
    if not managers:
        return list(DEFAULT_MANAGERS)
    normalized: List[str] = []
    for manager in managers:
        key = manager.lower()
        if key not in VALID_MANAGERS:
            raise typer.BadParameter(
                _(
                    'Invalid manager "[yellow]{manager}[/yellow]". Choose from: {choices}'
                ).format(
                    manager=manager,
                    choices=', '.join(sorted(VALID_MANAGERS)),
                )
            )
        if key not in normalized:
            normalized.append(key)
    return normalized


@app.callback(invoke_without_command=True)
def edit_favorites(
    ctx: typer.Context,
    managers: Optional[List[str]] = typer.Option(
        None,
        '--manager',
        '-m',
        help=_('Limit selection to specific managers (apt, flatpak, snap).'),
    ),
):
    """
    Launches the favorite application picker.
    """
    if ctx.invoked_subcommand is not None:
        return

    questionary = _require_questionary()
    from easyinstaller.styles.styles import custom_style

    normalized_managers = _normalize_manager_options(managers)
    packages = unified_lister(normalized_managers)
    packages = filter_user_app_packages(packages)

    if not packages:
        console.print(
            _(
                '[yellow]No applications detected for the selected managers.[/yellow]'
            )
        )
        raise typer.Exit(0)

    current_favorites = load_favorites()
    choice_map = {}
    choices = []
    for pkg in packages:
        key = _package_key(pkg)
        choice_map[key] = pkg
        choices.append(
            questionary.Choice(
                title=_choice_title(pkg),
                value=key,
                checked=is_favorite(pkg, current_favorites),
            )
        )

    answer = questionary.checkbox(
        _('Select your favorite applications:'),
        choices=choices,
        style=custom_style,
    ).ask()

    if answer is None:
        console.print(
            _('[yellow]Selection cancelled. Favorites unchanged.[/yellow]')
        )
        raise typer.Exit(0)

    selected_packages = [choice_map[key] for key in answer]
    favorites = _build_favorites_payload(selected_packages)
    save_favorites(favorites)

    console.print(
        _(
            '[bold green]Favorite list updated ({count} applications).[/bold green]'
        ).format(count=favorites_count(favorites))
    )


@app.command('list')
def list_favorites():
    """
    Displays the current favorites.
    """
    favorites = load_favorites()
    total = favorites_count(favorites)
    if total == 0:
        console.print(_('[yellow]No favorites saved yet.[/yellow]'))
        return

    table = Table(
        title=_('Favorite applications'),
        show_header=True,
        header_style='bold magenta',
    )
    table.add_column(_('Manager'), style='cyan')
    table.add_column(_('Name'))
    table.add_column(_('Version'))

    for manager, entries in favorites.items():
        for entry in entries:
            table.add_row(
                manager,
                entry.get('name', ''),
                entry.get('version') or '',
            )

    console.print(table)


@app.command('clear')
def clear_favorites_command(
    confirm: bool = typer.Option(
        False,
        '--yes',
        '-y',
        help=_('Skip confirmation prompt and clear favorites immediately.'),
    )
):
    """
    Removes all saved favorites.
    """
    favorites = load_favorites()
    if favorites_count(favorites) == 0:
        console.print(_('[yellow]Favorites list is already empty.[/yellow]'))
        return

    proceed = confirm
    if not confirm:
        proceed = typer.confirm(
            _('Remove all favorite applications?'),
            default=False,
        )

    if not proceed:
        console.print(_('[yellow]Operation cancelled.[/yellow]'))
        return

    clear_favorites()
    console.print(_('[bold green]Favorites cleared.[/bold green]'))
