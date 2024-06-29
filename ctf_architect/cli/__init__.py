from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ctf_architect.cli.challenge import challenge_app
from ctf_architect.cli.docker import docker_app
from ctf_architect.cli.mapping import mapping_app
from ctf_architect.cli.stats import stats_app
from ctf_architect.core.constants import CTF_CONFIG_FILE
from ctf_architect.core.initialize import init_no_config, init_with_config

console = Console()


app = typer.Typer()
app.add_typer(challenge_app, name="challenge")
app.add_typer(docker_app, name="docker")
app.add_typer(mapping_app, name="mapping")
app.add_typer(stats_app, name="stats")


@app.command()
def init(
    starting_port: int = typer.Option(
        None, "--starting-port", "-p", help="The starting port for the CTF Services"
    ),
    config_only: bool = typer.Option(
        False, "--config-only", "-c", help="Only create the config file."
    ),
):
    """
    Initialize a new CTF repository.
    """

    # Check if the config file already exists
    if Path(CTF_CONFIG_FILE).exists():
        if config_only:
            console.print(
                "A config file already exists. Exiting...", style="bright_red"
            )

        if not Confirm.ask(
            "[cyan]A config file already exists. Do you want to use this config?[/]"
        ):
            console.print("Aborting...", style="bright_red")
            return

        try:
            init_with_config()
        except ValueError as e:
            console.print(f"Error initializing the CTF repo: {e}", style="bright_red")
            return
        else:
            console.print("CTF repo initialized successfully!", style="bright_green")

    else:
        ctf_name = None
        while not ctf_name:
            ctf_name = Prompt.ask("[cyan]Enter the name of the CTF[/]")

        if starting_port is None:
            starting_port = IntPrompt.ask(
                "[cyan]Starting port for the CTF Services[/]", default=8000
            )

        # Get the categories, difficulties and extras from the user
        categories = []
        difficulties = []
        extras = []

        try:
            console.rule("[bright_yellow]CTF Categories[/bright_yellow]")

            console.print(
                "Enter the categories for the CTF (one per line, empty line to stop).",
                style="bright_cyan",
            )

            while True:
                category = Prompt.ask(
                    "[cyan]Category name[/]", default="", show_default=False
                )
                if category == "":
                    break
                categories.append(category.lower())

                console.print(f"Category {category} added.\n", style="green")

            if len(categories) == 0:
                console.print("No categories specified. Exiting...", style="bright_red")
                return
            else:
                console.print("Categories:", style="bright_green")
                for category in categories:
                    console.print(f"  - {category}", style="green")

            console.rule("[bright_yellow]CTF Difficulties[/bright_yellow]")

            console.print(
                "Enter the difficulties for the CTF (empty name to stop).",
                style="bright_cyan",
            )

            while True:
                name = Prompt.ask(
                    "[cyan]Difficulty name[/]", default="", show_default=False
                )
                if name == "":
                    break
                value = IntPrompt.ask("[cyan]Difficulty value[/]", default=500)
                difficulties.append({"name": name.lower(), "value": value})

                console.print(
                    f"Difficulty {name} added. ({value} points)\n", style="green"
                )

            if len(difficulties) == 0:
                console.print(
                    "No difficulties specified. Exiting...", style="bright_red"
                )
                return
            else:
                console.print("Difficulties:", style="bright_green")
                for difficulty in difficulties:
                    console.print(
                        f"  - {difficulty['name']} ({difficulty['value']} points)",
                        style="green",
                    )

            console.rule("[bright_yellow]Extra Fields[/bright_yellow]")

            console.print(
                "Enter any extra fields challenges should specify (one per line, empty line to stop).",
                style="bright_cyan",
            )

            while True:
                extra = Prompt.ask(
                    "[cyan]Extra field[/]", default="", show_default=False
                )
                if extra == "":
                    break
                extras.append(extra)

                console.print(f"Extra field {extra} added.\n", style="green")
        except (KeyboardInterrupt, EOFError):
            console.print("\nAborting...", style="bright_red")
            return

        # Show panel of current configuration and ask for confirmation
        # If the user confirms, initialize the CTF repo

        config_text = "[bright_cyan]Categories:[/]\n"
        for category in categories:
            config_text += f"[cyan]  - {category}[/]\n"
        config_text += "\n[bright_cyan]Difficulties:[/]\n"
        for difficulty in difficulties:
            config_text += (
                f"[cyan]  - {difficulty['name']} ({difficulty['value']} points)[/]\n"
            )
        config_text += "\n[bright_cyan]Extras:[/]\n"
        for extra in extras:
            config_text += f"[cyan]  - {extra}[/]\n"

        config_text += f"\n[bright_cyan]Starting Port:[/]\n[cyan]  - {starting_port}[/]"

        console.print(
            Panel(
                config_text,
                title=f"[bright_yellow]{ctf_name} Configuration[/bright_yellow]",
                border_style="green",
            )
        )

        if not Confirm.ask("[cyan]Is this configuration correct?[/]"):
            console.print("Aborting...", style="bright_red")
            return

        try:
            init_no_config(
                name=ctf_name,
                categories=categories,
                difficulties=difficulties,
                starting_port=starting_port,
                extras=extras,
                config_only=config_only,
            )
        except ValueError as e:
            console.print(f"Error initializing the CTF repo:\n{e}", style="bright_red")
            return
        else:
            console.print("CTF repo initialized successfully.", style="bright_green")
