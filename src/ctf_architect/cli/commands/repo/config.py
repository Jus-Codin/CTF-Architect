from __future__ import annotations

from pathlib import Path

from cyclopts import App

from ctf_architect.cli.ui.components import create_repo_config_panels
from ctf_architect.cli.ui.console import console
from ctf_architect.core.exceptions import NotInChallengeRepositoryError
from ctf_architect.core.repo import Repo

app = App(name="config", group="Subcommands")


@app.default
@app.command
def show():
    """Show the challenge repository configuration."""
    try:
        repo = Repo.from_path(Path.cwd())
    except NotInChallengeRepositoryError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    config = repo.ctf_config

    for panel in create_repo_config_panels(
        name=config.name,
        flag_format=config.flag_format,
        starting_port=config.starting_port,
        categories=config.categories,
        difficulties=config.difficulties,
        extras=config.extras,
    ):
        console.print(panel)
