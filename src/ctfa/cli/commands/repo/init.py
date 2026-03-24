from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ResolvedExistingDirectory


def command(
    location: Annotated[ResolvedExistingDirectory, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    bare: Annotated[bool, Parameter(name=["--bare", "-b"], negative="")] = False,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
    name: Annotated[str | None, Parameter(name=["--name", "-n"])] = None,
    categories: Annotated[list[str] | None, Parameter(name=["--category", "-c"], consume_multiple=True)] = None,
    difficulties: Annotated[list[str] | None, Parameter(name=["--difficulty", "-d"], consume_multiple=True)] = None,
    flag_format: Annotated[str | None, Parameter(name=["--flag-format", "-f"])] = None,
    starting_port: Annotated[int | None, Parameter(name=["--starting-port", "-s"])] = None,
):
    """Initialise a new challenge repository.

    Args:
        location (ResolvedExistingDirectory, optional): The location to create the repository in
        bare (bool, optional): Initialise the CTF Config file only
        no_interactive (bool, optional): Do not prompt for any missing information
        name (str | None, optional): Name of the repository
        categories (list[str] | None, optional): Categories to include
        difficulties (list[str] | None, optional): Difficulties to include
        flag_format (str | None, optional): Flag format to use
        starting_port (int | None, optional): Starting port for services
    """
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.prompts import select
    from ctfa.constants import CTF_CONFIG_FILE
    from ctfa.core.repository import ChallengeRepository

    repo_config = None

    if (location / CTF_CONFIG_FILE).exists():
        if bare:
            console.print(f"A CTF Config file already exists at '{location}'. Exiting...", style="ctfa.error")
            return

        choice = select(
            f"A CTF Config file already exists at '{location}'. What would you like to do?",
            choices=[
                "Use existing CTF Config file",
                "Overwrite existing CTF Config file",
                "Abort",
            ],
        ).ask()

        if choice == "Abort":
            console.print("Aborting...", style="ctfa.error")
            return

        elif choice == "Use existing CTF Config file":
            if any([name, categories, difficulties, flag_format, starting_port]):
                console.print(
                    "Ignoring provided repository details since an existing CTF Config file is being used...",
                    style="ctfa.warning",
                )

            repo_config = ChallengeRepository.load_config_file(location / CTF_CONFIG_FILE)

        elif choice == "Overwrite existing CTF Config file":
            console.print("Overwriting existing CTF Config file...", style="ctfa.warning")

    if repo_config is None:
        from ctfa.cli.ui.flows import ask_ctf_config_details

        _repo_config = ask_ctf_config_details(
            name=name,
            categories=categories,
            difficulties=difficulties,
            flag_format=flag_format,
            starting_port=starting_port,
            interactive=not no_interactive,
        )

        if _repo_config is None:
            console.print("Aborting...", style="ctfa.error")
            return

        repo_config = _repo_config

    if bare:
        ChallengeRepository.create_config_only(location, repo_config)
        console.print(f"CTF Config file created at {location / CTF_CONFIG_FILE}", style="ctfa.success")
    else:
        repo = ChallengeRepository.create(location, repo_config)
        console.print(f"Challenge Repository '{repo_config.name}' initialised at {repo.location}", style="ctfa.success")
