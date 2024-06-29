from __future__ import annotations

import time
from pathlib import Path
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ctf_architect.chall_architect.create import create_challenge
from ctf_architect.chall_architect.utils import get_config, is_valid_service_folder

console = Console()


def prompt(
    message: str, allow_empty: bool = False, method: Callable = Prompt.ask, **kwargs
) -> str | int:
    """
    Prompt the user for a string input.

    Args:
      message (str): The message to show to the user.
      allow_empty (bool, optional): Whether to allow an empty input. Defaults to False.
      method (Callable, optional): The method to use to prompt the user. Defaults to Prompt.ask.

    Returns:
      str: The user's input.
    """
    if not allow_empty:
        while True:
            res = method(message, **kwargs)
            if res != "":
                return res
            else:
                console.print("This field cannot be empty.", style="bright_red")
    else:
        return method(message, **kwargs)


def get_ctf_config():
    """
    Prompts the user for the CTF config.
    """
    console.rule(":gear: [bright_yellow]CTF Config[/bright_yellow] :gear:")

    while True:
        console.print("Please select the CTF config file.", style="cyan")
        time.sleep(1)

        config_file = askopenfilename(
            title="Select the CTF Config file",
            filetypes=[
                ("TOML files", "*.toml")
            ],  # Still a bit of hardcoding here, but should be fine
        )

        if config_file == "":
            return None

        try:
            config = get_config(config_file)
        except Exception as e:
            console.print(f"Error loading CTF config file: {e}", style="bright_red")
            return

        # Print config in a panel
        config_string = "[bright_cyan]Categories:[/bright_cyan][cyan]"
        for category in config.categories:
            config_string += f"\n  - {category.capitalize()}"

        config_string += "\n\n[/cyan][bright_cyan]Difficulties:[/bright_cyan][cyan]"
        for difficulty in config.difficulties:
            config_string += (
                f"\n  - {difficulty.name.capitalize()} ({difficulty.value})"
            )

        config_string += "\n\n[/cyan][bright_cyan]Extra Fields:[/bright_cyan][cyan]"
        if config.extras is None:
            config_string += "\n  None"
        else:
            for extra in config.extras:
                config_string += f"\n  - {extra}"

        config_string += f"\n\n[/cyan][bright_cyan]Starting Port: [/bright_cyan][cyan]{config.starting_port}[/cyan]"

        console.print(
            Panel(
                config_string,
                border_style="green",
                title=f"[bright_yellow]{config.name} Config[/bright_yellow]",
            )
        )

        if Confirm.ask("[cyan]Is this the correct config?[/]"):
            return config

        # Add spacing
        console.print()


def get_description():
    """
    Prompts the user for the description of the challenge.
    This allows users to enter multiple lines, and exit when EOF is entered.
    """

    console.print(
        ":rocket: [cyan][2/6] Please enter the challenge description. Press Ctrl+D (or Ctrl+Z on Windows) on an empty line to finish.[/]",
        highlight=False,
    )

    description = []
    while True:
        try:
            line = input(">>> ")
            description.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            return None

    return "\n".join(description)


def get_solution_files():
    """
    Prompts the user for the solution files.
    """
    console.rule(
        ":file_folder: [bright_yellow]Please select the solution files for the challenge.[/] :file_folder:"
    )

    time.sleep(1)

    return askopenfilenames(title="Select the solution files for the challenge")


def get_flags() -> list[dict[str, str | bool]]:
    """
    Prompts the user for the flags of the challenge.
    """
    console.rule(
        ":triangular_flag: [bright_yellow]Challenge Flags[/] :triangular_flag:"
    )

    flags = []
    while True:
        regex = Confirm.ask(":triangular_flag: [cyan]Is the flag a regex flag?[/]")
        case_sensitive = Confirm.ask(
            ":triangular_flag: [cyan]Is the flag case-sensitive?[/]"
        )
        flag = prompt(":triangular_flag: [cyan]Enter the flag[/]")
        flags.append({"flag": flag, "regex": regex, "case_sensitive": case_sensitive})

        if not Confirm.ask("[cyan]Do you want to add another flag?[/]"):
            break

        # Add spacing between the flags
        console.print()

    return flags


def get_hints() -> list[dict[str, int | str | list[int]]] | None:
    """
    Prompts the user for hints.
    """
    console.rule(":light_bulb: [bright_yellow]Challenge Hints[/] :light_bulb:")

    if not Confirm.ask(":light_bulb: [cyan]Does the challenge have hints?[/]"):
        return None

    # Add spacing
    console.print()

    hints = []
    while True:
        content = prompt(":light_bulb: [cyan]Please enter the hint content[/]")
        cost = prompt(
            ":light_bulb: [cyan]Please enter the hint cost[/]", method=IntPrompt.ask
        )

        requirements = None
        if len(hints) > 0:
            if Confirm.ask(
                ":light_bulb: [cyan]Do you want to add a hint requirement?[/]"
            ):
                # print the current hints in a list
                console.print("\n[green]Hints:[/]")
                for i, hint in enumerate(hints):
                    console.print(
                        f"  [green]{i}. {hint['content']} ({hint['cost']})[/]"
                    )

                valid = False
                while not valid:
                    requirements = prompt(
                        ":light_bulb: [cyan]Please enter the hint requirements (comma-separated)[/]"
                    )
                    requirements = [int(req) for req in requirements.split(",")]

                    for req in requirements:
                        if req >= len(hints):
                            console.print(
                                f"[bright_red]Invalid hint requirement: {req}[/]"
                            )
                            break
                    else:
                        valid = True

        hints.append({"content": content, "cost": cost, "requirements": requirements})

        if not Confirm.ask("[cyan]Do you want to add another hint?[/]"):
            break

        # Add spacing
        console.print()

    return hints


def get_files() -> list[Path | str] | None:
    """
    Prompts the user for files and URLs.
    """
    console.rule(":file_folder: [bold yellow]Challenge Files[/] :file_folder:")

    if not Confirm.ask(
        ":file_folder: [cyan]Does the challenge have files to give to players?[/]"
    ):
        return None

    # Add spacing
    console.print()

    files = []

    if Confirm.ask(":file_folder: [cyan]Are there any files from URLs?[/]"):
        while True:
            url = prompt(":file_folder: [cyan]Please enter the URL[/]")
            files.append(url)

            if not Confirm.ask("[cyan]Do you want to add another URL?[/]"):
                break

            # Add spacing
            console.print()

    # Add spacing
    console.print()

    if Confirm.ask(":file_folder: [cyan]Are there any files from the local system?[/]"):
        time.sleep(1)
        local_files = askopenfilenames(title="Select the files for the challenge")
        if local_files == "":
            return ""
        else:
            for file in local_files:
                files.append(Path(file))

    return files


def get_requirements() -> list[str] | None:
    """
    Prompts the user for the challenge requirements.
    """
    console.rule(":gear: [bold yellow]Challenge Requirements[/] :gear:")

    if not Confirm.ask(":gear: [cyan]Does the challenge have requirements?[/]"):
        return None

    # Add spacing
    console.print()

    requirements = []
    while True:
        requirement = prompt(":gear: [cyan]Please enter a requirement[/]")
        requirements.append(requirement)

        if not Confirm.ask("[cyan]Do you want to add another requirement?[/]"):
            break

        # Add spacing
        console.print()

    return requirements


def get_services() -> list[dict[str, str | int | dict[str, str | int]]] | None:
    """
    Prompts the user for services.
    """
    console.rule(":gear: [bold yellow]Challenge Services[/] :gear:")

    if not Confirm.ask(":gear: [cyan]Does the challenge have services?[/]"):
        return None

    # Add spacing
    console.print()

    services = []
    while True:
        name = prompt(":gear: [cyan]Please enter the service name[/]")
        port = prompt(
            ":gear: [cyan]Please enter the service port[/]", method=IntPrompt.ask
        )
        service_type = prompt(
            ":gear: [cyan]Please enter the service type[/]",
            choices=["web", "nc", "ssh", "secret", "internal"],
        )
        console.print(f":gear: [cyan]Please select the service folder...[/]")
        path = askdirectory(title="Select the service folder")

        if path == "":
            # User cancelled, abort
            console.print("[bright_red]No folder selected, aborting...[/bright_red]")
            return ""

        if not is_valid_service_folder(path):
            console.print("[bright_red]Invalid service folder, try again.[/bright_red]")
            continue

        extras = {}
        if Confirm.ask(":gear: [cyan]Does the service have any extra fields?[/]"):
            while True:
                key = prompt(":gear: [cyan]Please enter the extra field key[/]")
                value = prompt(":gear: [cyan]Please enter the extra field value[/]")
                extras[key] = value

                if not Confirm.ask("[cyan]Do you want to add another extra field?[/]"):
                    break

        services.append(
            {
                "name": name,
                "path": path,
                "port": port,
                "type": service_type,
                "extras": extras,
            }
        )

        if not Confirm.ask("[cyan]Do you want to add another service?[/]"):
            break

        # Add spacing
        console.print()

    return services


def create():
    """
    Main function to create a challenge.
    """

    config = get_ctf_config()

    if config is None:
        console.print("[bright_red]No config selected, aborting...[/bright_red]")
        return

    categories = config.categories
    difficulties = config.difficulties

    console.rule(":rocket: [bright_yellow]Challenge Creation[/] :rocket:")

    name = prompt(
        ":rocket: [cyan][1/6] Please enter the challenge name (case-insensitive)[/]"
    )

    description = get_description()
    if description is None:
        # User cancelled, abort
        console.print("[bright_red]Aborting...[/bright_red]")
        return

    # Print the categories in a list
    console.print("\n[bright_cyan]Categories:[/]")
    for i, category in enumerate(categories):
        console.print(f"[bright_cyan]{i+1}. {category.capitalize()}[/]")

    while True:
        category = prompt(
            f"\n:rocket: [cyan][3/6] Please choose the challenge category \[1-{len(categories)}][/]",
            method=IntPrompt.ask,
        )
        if 1 > category > len(categories):
            console.print("[bright_red]Please choose a valid category.[/]\n")
        else:
            category = categories[category - 1].capitalize()
            break

    console.print(f"[green]Category selected: {category}[/green]\n")

    # Print the difficulties in a list
    console.print("[bright_cyan]Difficulties:[/]")
    for i, difficulty in enumerate(difficulties):
        console.print(
            f"[bright_cyan]{i+1}. {difficulty.name.capitalize()} ({difficulty.value})[/]"
        )

    while True:
        difficulty = prompt(
            f"\n:rocket: [cyan][4/6] Please choose the challenge difficulty \[1-{len(difficulties)}][/]",
            method=IntPrompt.ask,
        )
        if 1 > difficulty > len(difficulties):
            console.print("[bright_red]Please choose a valid difficulty.[/]\n")
        else:
            difficulty = difficulties[difficulty - 1]
            difficulty = difficulty.name.capitalize()
            break

    console.print(f"[green]Difficulty selected: {difficulty}[/green]\n")

    author = prompt("\n:rocket: [cyan][5/6] Please enter your name[/]")

    extra_fields = {}
    if config.extras is not None:
        for extra_field in config.extras:
            extra = prompt(
                f"\n:rocket: [cyan][6/6] Please enter info for {extra_field}[/]"
            )
            console.print(f"[green]{extra_field.capitalize()}: {extra}[/green]")
            extra_fields[extra_field] = extra
    else:
        console.print("\n:rocket: [cyan][6/6] No extra fields to fill, skipping...[/]")

    solution_files = get_solution_files()
    if solution_files == "":
        # User cancelled, abort
        console.print("[bright_red]No files selected, aborting...[/bright_red]")
        return

    elif solution_files is not None:
        solution_files = [Path(file) for file in solution_files]

        console.print("[green]Solution files selected: [/green]")
        for file in solution_files:
            console.print(f"  [green]{file}[/]")

    flags = get_flags()

    hints = get_hints()

    files = get_files()
    if files == "" or files == []:
        # User cancelled, abort
        console.print("[bright_red]No files selected, aborting...[/bright_red]")
        return

    elif files is not None:
        console.print("[green]Files selected: [/green]")
        for file in files:
            console.print(f"[light_green]- {file}[/]")

    services = get_services()

    if services and Confirm.ask(
        ":rocket: [cyan]Does the service(s) need a Docker Compose file?[/]"
    ):
        # Ask for a docker-compose file
        console.print(
            "[bright_cyan]Please select the Docker Compose file for the services[/bright_cyan]"
        )
        docker_compose = askopenfilename(
            title="Select the Docker Compose file for the services",
            filetypes=[("Docker Compose files", "*.yml")],
        )
        if docker_compose == "":
            console.print(
                "[bright_red]No Docker Compose file selected, aborting...[/bright_red]"
            )
            return
        else:
            docker_compose = Path(docker_compose)
    else:
        docker_compose = None

    console.print()

    requirements = get_requirements()

    # console.print the challenge details
    info_string = f"[cyan][bold]Name:[/bold] {name}\n"
    info_string += f"[bold]Description:[/bold] {description}\n"
    info_string += f"[bold]Category:[/bold] {category}\n"
    info_string += f"[bold]Difficulty:[/bold] {difficulty}\n"
    info_string += f"[bold]Author:[/bold] {author}\n\n"

    info_string += "[bold]Extra Fields:[/bold]\n"
    for field_name, field in extra_fields.items():
        info_string += f"[bold]{field_name.capitalize()}:[/bold] {field}\n"
    else:
        info_string += "None\n"
    info_string += "\n"

    info_string += f"[bold]Solution Files:[/bold]\n"
    for file in solution_files:
        info_string += f"- {file.as_posix()}\n"
    info_string += "\n"

    info_string += (
        f"[bold]Flags:[/bold] {', '.join([flag['flag'] for flag in flags])}\n\n"
    )

    info_string += "[bold]Hints:[/bold]\n"
    if hints is not None:
        for hint in hints:
            info_string += f"- {hint['content']} ({hint['cost']})\n"
    else:
        info_string += "None\n"
    info_string += "\n"

    info_string += "[bold]Files:[/bold]\n"
    if files is not None:
        for file in files:
            if isinstance(file, Path):
                info_string += f"- {file.as_posix()}\n"
            else:
                info_string += f"- [u blue link={file}]{file}[/]\n"
    else:
        info_string += "None\n"
    info_string += "\n"

    info_string += "[bold]Services:[/bold]\n"
    if services is not None:
        for service in services:
            info_string += f"- {service['name']} ({service['type']})\n"
    else:
        info_string += "None\n"
    info_string += "\n"

    info_string += "[bold]Docker Compose:[/bold]\n"
    if docker_compose is not None:
        info_string += f"- {docker_compose.as_posix()}\n"
    else:
        info_string += "None\n"

    info_string += "[bold]Requirements:[/bold]\n"
    if requirements is not None:
        for requirement in requirements:
            info_string += f"- {requirement}\n"
    else:
        info_string += "None\n"

    info_string += "[/cyan]"

    console.print(
        Panel(
            info_string,
            title="[bright_yellow]Challenge Details[/bright_yellow]",
            border_style="green",
        )
    )

    # Confirm the challenge creation
    if not Confirm.ask("[cyan]Do you want to create the challenge?[/]"):
        console.print("[bright_red]Aborting...[/bright_red]")
        return

    # Create the challenge
    challenge_path = create_challenge(
        name=name,
        description=description,
        category=category,
        difficulty=difficulty,
        author=author,
        extras=extra_fields,
        solution_files=solution_files,
        flags=flags,
        hints=hints,
        files=files,
        services=services,
        docker_compose=docker_compose,
        requirements=requirements,
    )

    console.print(
        f"[green]Successfully created challenge `{name}` at `{challenge_path.resolve()}`[/green]"
    )
