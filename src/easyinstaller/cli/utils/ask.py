import questionary
from rich.console import Console

from easyinstaller.styles.styles import custom_style

console = Console()

CANCEL_VALUE = {'id': '__CANCEL__'}


def ask_user_to_select_packages(choices: list[dict]) -> list[dict] | None:
    """Given a list of packages, asks the user to select one or more."""
    if not choices:
        console.print('[yellow]No packages found.[/yellow]')
        return None

    formatted_choices = [
        {
            'name': f"{choice['name']} [{choice['source']}] - {choice.get('summary') or choice.get('version', '')}",
            'value': choice,
            'checked': False,
        }
        for choice in choices
    ]

    formatted_choices.append(questionary.Separator('-' * 15))
    formatted_choices.append(
        {'name': 'Cancel', 'value': CANCEL_VALUE, 'checked': False}
    )

    selected_choices = questionary.checkbox(
        'Found multiple packages. Please select one or more to install:',
        choices=formatted_choices,
        style=custom_style,
    ).ask()

    # If user cancels by pressing Enter or selecting the 'Cancel' option
    if not selected_choices or CANCEL_VALUE in selected_choices:
        console.print('[red]Installation cancelled.[/red]')
        return None

    return selected_choices
