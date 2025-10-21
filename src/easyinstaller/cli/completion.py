import typer
from rich.console import Console

app = typer.Typer(
    name='completion',
    help='Manages shell completion for easyinstaller.',
    no_args_is_help=True,
)
console = Console()


@app.command(name='install')
def install_completion(
    shell: str = typer.Argument(
        ...,
        help='The shell to install completion for (e.g., bash, zsh, fish).',
    )
):
    """
    Installs shell completion for the specified shell.
    """
    script = typer.main.get_completion_script(app, shell)
    if not script:
        console.print(
            f'[red]Error:[/red] Could not generate completion script for shell: [yellow]{shell}[/yellow]'
        )
        raise typer.Exit(1)

    console.print(
        f"To install completion for [bold green]{shell}[/bold green], add the following to your shell's config file (e.g., ~/.bashrc, ~/.zshrc):\n"
    )
    console.print(f'```bash\n{script}\n```\n')
    console.print(
        f'Then, reload your shell (e.g., `source ~/.bashrc` or `exec {shell}`).'
    )


@app.command(name='show')
def show_completion(
    shell: str = typer.Argument(
        ..., help='The shell to show completion for (e.g., bash, zsh, fish).'
    )
):
    """
    Shows the shell completion script for the specified shell.
    """
    script = typer.main.get_completion_script(app, shell)
    if not script:
        console.print(
            f'[red]Error:[/red] Could not generate completion script for shell: [yellow]{shell}[/yellow]'
        )
        raise typer.Exit(1)
    console.print(script)


if __name__ == '__main__':
    app()
