import typer

from easyinstaller.cli import add as add_app
from easyinstaller.cli import remove as rm_app
from easyinstaller.cli import flatpak as flatpak_app

app = typer.Typer(
    name="ei",
    help="A universal installation manager for Linux.",
    add_completion=False,
)

app.add_typer(add_app.app, name="add")
app.add_typer(rm_app.app, name="rm")
app.add_typer(flatpak_app.app, name="flatpak")


@app.callback()
def main():
    """
    A universal installation manager for Linux.
    """
    pass


if __name__ == "__main__":
    app()
