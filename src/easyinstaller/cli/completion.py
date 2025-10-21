import typer
from rich.console import Console

from easyinstaller.i18n.i18n import _

app = typer.Typer(
    name='completion',
    help=_('Manages shell completion for easyinstaller.'),
    no_args_is_help=True,
)
console = Console()


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
    script = typer.main.get_completion_script(app, shell)
    if not script:
        console.print(
            _(
                '[red]Error:[/red] Could not generate completion script for shell: [yellow]{shell}[/yellow]'
            ).format(shell=shell)
        )
        raise typer.Exit(1)

    console.print(
        _(
            "To install completion for [bold green]{shell}[/bold green], add the following to your shell's config file (e.g., ~/.bashrc, ~/.zshrc):\n"
        ).format(shell=shell)
    )
    console.print(f'```bash\n{script}\n```\n')
    console.print(
        _(
            'Then, reload your shell (e.g., `source ~/.bashrc` or `exec {shell}`).'
        ).format(shell=shell)
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
    script = typer.main.get_completion_script(app, shell)
    if not script:
        console.print(
            _(
                '[red]Error:[/red] Could not generate completion script for shell: [yellow]{shell}[/yellow]'
            ).format(shell=shell)
        )
        raise typer.Exit(1)
    console.print(script)


if __name__ == '__main__':
    app()
