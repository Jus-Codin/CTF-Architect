from __future__ import annotations

from cyclopts import App

from ctf_architect.cli.ui.components import create_repo_config_panels
from ctf_architect.cli.ui.console import console
from ctf_architect.core.repo import load_repo_config

app = App(name="config", group="Subcommands")


@app.default
@app.command
def show():
    """Show the challenge repository configuration."""
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    for panel in create_repo_config_panels(
        name=config.name,
        flag_format=config.flag_format,
        starting_port=config.starting_port,
        categories=config.categories,
        difficulties=config.difficulties,
        extras=config.extras,
    ):
        console.print(panel)
