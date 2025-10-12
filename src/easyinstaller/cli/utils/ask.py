import questionary
from rich.console import Console

console = Console()


def ask_user_to_select_package(choices: list[dict]) -> dict | None:
    """Given a list of packages, asks the user to select one."""
    if not choices:
        console.print("[yellow]No packages found.[/yellow]")
        return None

    # Format choices for questionary
    formatted_choices = [
        f"{choice['name']} [{choice['source']}] - {choice['summary']}"
        for choice in choices
    ]
    formatted_choices.append(questionary.Separator())
    formatted_choices.append("Cancel")

    selected_choice_str = questionary.select(
        "Found multiple packages. Please select one to install:",
        choices=formatted_choices,
        use_indicator=True,
    ).ask()

    if not selected_choice_str or selected_choice_str == "Cancel":
        console.print("[red]Installation cancelled.[/red]")
        return None

    # Find the original dictionary corresponding to the selected string
    for choice in choices:
        if selected_choice_str.startswith(f"{choice['name']} [{choice['source']}]"):
            return choice
    
    return None # Should not be reached
