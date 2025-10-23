from typing import Dict

import typer
from rich.console import Console
from typer._completion_shared import Shells, get_completion_script

from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='completion',
    help=_('Manages shell completion for easyinstaller.'),
    no_args_is_help=True,
)
console = Console()

SUPPORTED_SHELLS = {shell.value for shell in Shells}
SHELL_ALIASES: Dict[str, str] = {
    'powershell': 'pwsh',
}


def _normalize_shell(shell: str) -> str:
    normalized = shell.lower()
    normalized = SHELL_ALIASES.get(normalized, normalized)

    if normalized not in SUPPORTED_SHELLS:
        supported = ', '.join(sorted(SUPPORTED_SHELLS))
        raise typer.BadParameter(
            _(
                'Shell "[yellow]{shell}[/yellow]" is not supported. Supported shells: {supported}'
            ).format(shell=shell, supported=supported)
        )

    return normalized


def _build_completion_script(shell: str) -> str:
    normalized = _normalize_shell(shell)
    from easyinstaller.main import app as main_app

    prog_name = main_app.info.name or 'ei'
    complete_var = f'_{prog_name.replace("-", "_").upper()}_COMPLETE'

    return get_completion_script(
        prog_name=prog_name, complete_var=complete_var, shell=normalized
    )


@app.command(name='install')
def install_completion(
    shell: str = typer.Argument(
        ...,
        help=_('The shell to install completion for (e.g., bash, zsh, fish).'),
    )
):
    """
    Installs shell completion for the specified shell.
    """
    normalized_shell = _normalize_shell(shell)
    script = _build_completion_script(normalized_shell)

    console.print(
        _(
            "To install completion for [bold green]{shell}[/bold green], add the following to your shell's config file (e.g., ~/.bashrc, ~/.zshrc):\n"
        ).format(shell=normalized_shell)
    )
    console.print(f'```{normalized_shell}\n{script}\n```\n')
    console.print(
        _(
            'Then, reload your shell (e.g., `source ~/.bashrc` or `exec {shell}`).'
        ).format(shell=normalized_shell)
    )


@app.command(name='show')
def show_completion(
    shell: str = typer.Argument(
        ...,
        help=_('The shell to show completion for (e.g., bash, zsh, fish).'),
    )
):
    """
    Shows the shell completion script for the specified shell.
    """
    normalized_shell = _normalize_shell(shell)
    script = _build_completion_script(normalized_shell)
    console.print(script)


if __name__ == '__main__':
    app()
