import datetime
import json
import os

import typer
from rich.console import Console
from rich.table import Table

from easyinstaller.core.history_handler import get_history_file_path

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def show_history():
    """
    Displays the installation and removal history.
    """
    history_file = get_history_file_path()

    if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
        console.print('[yellow]No history found.[/yellow]')
        return

    table = Table(
        title='EasyInstaller History',
        show_header=True,
        header_style='bold magenta',
        expand=True,
    )
    table.add_column('Date', style='dim', width=12)
    table.add_column('Time', style='dim', width=10)
    table.add_column('Action', width=10)
    table.add_column('Package')
    table.add_column('Manager', style='cyan')
    table.add_column('Details', justify='right')

    try:
        with open(history_file, 'r') as f:
            history_entries = [json.loads(line) for line in f]

        # Sort by timestamp descending (newest first)
        history_entries.sort(
            key=lambda x: x.get('timestamp', ''), reverse=True
        )

        for entry in history_entries:
            action = entry.get('action', 'N/A')
            package = entry.get('package', 'N/A')
            manager = entry.get('manager', 'N/A')
            timestamp_str = entry.get('timestamp')

            if timestamp_str:
                dt_object = datetime.datetime.fromisoformat(timestamp_str)
                date_str = dt_object.strftime('%Y-%m-%d')
                time_str = dt_object.strftime('%H:%M:%S')
            else:
                date_str, time_str = 'N/A', 'N/A'

            action_style = 'green' if action == 'install' else 'red'

            details = ''
            if action == 'install' and 'installed_packages' in entry:
                count = len(entry['installed_packages']) - 1
                if count > 0:
                    details = f"{count} dependenc{'ies' if count > 1 else 'y'}"
            elif action == 'remove' and 'removed_packages' in entry:
                count = len(entry['removed_packages']) - 1
                if count > 0:
                    details = f'{count} packages removed'

            table.add_row(
                date_str,
                time_str,
                f'[{action_style}]{action}[/{action_style}]',
                package,
                manager,
                details,
            )

        console.print(table)

    except (IOError, json.JSONDecodeError) as e:
        console.print(f'[bold red]Error reading history file:[/bold red] {e}')


if __name__ == '__main__':
    app()
