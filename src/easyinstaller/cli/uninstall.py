import os
import subprocess

import typer
from rich.console import Console

app = typer.Typer(
    name='uninstall',
    help='Uninstalls the easyinstaller (ei) application from the system.',
    no_args_is_help=True,
)
console = Console()

UNINSTALL_SCRIPT_PATH = '/usr/local/share/easyinstaller/uninstall.sh'


@app.callback(invoke_without_command=True)
def uninstall():
    """
    Uninstalls the easyinstaller (ei) application from the system.
    """
    console.print(
        '[bold yellow]Attempting to uninstall easyinstaller...[/bold yellow]'
    )

    if not os.path.exists(UNINSTALL_SCRIPT_PATH):
        console.print(
            f'[red]Error:[/red] Uninstall script not found at [cyan]{UNINSTALL_SCRIPT_PATH}[/cyan].'
        )
        console.print(
            'Easyinstaller may not have been installed with the install.sh script.'
        )
        raise typer.Exit(code=1)

    console.print(f'Found uninstall script. Running with sudo...\n---')

    try:
        # Using subprocess.run to stream output directly to the user's terminal
        process = subprocess.run(
            ['sudo', 'bash', UNINSTALL_SCRIPT_PATH],
            check=True,
        )
    except FileNotFoundError:
        # This case is unlikely if the os.path.exists check passed, but for safety
        console.print(
            f"[red]Error:[/red] Could not execute 'sudo'. Is it in your PATH?"
        )
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as e:
        console.print(
            f'[red]Error:[/red] The uninstall script failed with exit code {e.returncode}.\n---'
        )
        raise typer.Exit(code=e.returncode)
    except KeyboardInterrupt:
        console.print('\n[yellow]Uninstall cancelled by user.[/yellow]')
        raise typer.Exit(1)

    # The uninstall script itself prints success messages.


if __name__ == '__main__':
    app()
