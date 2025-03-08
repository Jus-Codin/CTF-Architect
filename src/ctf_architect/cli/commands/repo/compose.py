from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from ctf_architect.cli.ui.console import console
from ctf_architect.cli.ui.prompts import confirm
from ctf_architect.core.compose import create_compose_files, get_compose_file_path
from ctf_architect.core.repo import is_challenge_repo

app = App(
    name="compose",
    group="Subcommands",
    help="Commands to create compose files for challenges.",
)


@app.command
def generate(
    force: Annotated[bool, Parameter(name=["--force", "-f"], negative="")] = False,
):
    """Generate compose files for all challenges.

    Args:
        force: Force generation of compose files.
    """
    if not is_challenge_repo():
        console.print(
            "This is not a valid challenge repo. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    if not force and get_compose_file_path(Path.cwd()):
        if not confirm("This will overwrite the current compose file. Do you want to continue?").execute():
            return

    create_compose_files()
    console.print("Compose files generated successfully!", style="ctfa.success")
