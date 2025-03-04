from __future__ import annotations

from cyclopts import App
from rich.align import Align

from ctf_architect.cli.ui.components import create_mapping_table
from ctf_architect.cli.ui.console import console
from ctf_architect.cli.ui.prompts import confirm
from ctf_architect.core.port_mapping import (
    generate_port_mapping,
    load_port_mapping,
    save_port_mapping,
)
from ctf_architect.core.repo import is_challenge_repo

app = App(
    name="mapping",
    group="Subcommands",
    help="Commands to manage port mappings for challenge services",
)


@app.default
@app.command
def show():
    """Show the port mappings for challenge services"""
    try:
        mapping = load_port_mapping()
        table = create_mapping_table(mapping)
        console.print(Align.center(table, vertical="middle"))
    except FileNotFoundError:
        console.print(
            "Could not find port mapping file. Have you generated the port mapping?",
            style="ctfa.error",
        )


@app.command
def generate(yes: bool = False):
    """Generates port mappings for challenge services"""
    if not is_challenge_repo():
        console.print(
            "This is not a challenge repository. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    mapping = generate_port_mapping()

    table = create_mapping_table(mapping)
    console.print(table)

    # If --yes flag is not provided, ask for confirmation interactively
    if not yes:
        if not confirm("Do you want to save the port mapping?").execute():
            return

    save_port_mapping(mapping)
    console.print("Port mapping saved successfully", style="ctfa.success")
