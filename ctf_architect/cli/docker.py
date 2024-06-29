from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ctf_architect.core.challenge import is_challenge_repo
from ctf_architect.core.docker import create_compose_file

console = Console()


docker_app = typer.Typer()


@docker_app.callback()
def callback():
    """
    Commands to manage challenge services in the CTF repo.
    """


@docker_app.command("generate")
def docker_generate(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force generation of docker compose file."
    ),
):
    """
    Generate a docker compose file for all challenges.
    """

    if not is_challenge_repo():
        console.print(
            "Not a valid challenge repo. Are you in the right directory?",
            style="bright_red",
        )
        return

    if not force and Path("docker-compose.yml").exists():
        if not Confirm.ask(
            "This will overwrite the current docker-compose.yml file. Do you want to continue?"
        ):
            return

    try:
        create_compose_file()
    except Exception as e:
        console.print(
            f"An error occurred while generating the docker compose file: {e}",
            style="bright_red",
        )
        return
    else:
        console.print(
            "Docker compose file generated successfully.", style="bright_green"
        )
