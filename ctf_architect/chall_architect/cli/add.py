from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ctf_architect._console import console
from ctf_architect.core.challenge import get_chall_config, is_challenge_folder

app = typer.Typer()


@app.callback()
def callback():
    """Commands to add new items to a challenge"""


@app.command("dist")
def add_dist(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
    local_files: Annotated[
        list[Path] | None,
        typer.Option("--local-file", "-l", help="Local files of the challenge"),
    ] = None,
    remote_files: Annotated[
        list[str] | None,
        typer.Option("--remote-file", "-r", help="Remote files of the challenge"),
    ] = None,
):
    """Add a dist file to the challenge"""

    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )
        return

    try:
        config = get_chall_config(_cwd)
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            f"An error occurred while getting the challenge config: {e}", style="red"
        )
        return

    ...


@app.command("requirement")
def add_requirement(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
):
    """Add a requirement to the challenge"""

    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )
        return

    try:
        config = get_chall_config(_cwd)
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            f"An error occurred while getting the challenge config: {e}", style="red"
        )
        return

    ...


@app.command("flag")
def add_flag(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
):
    """Add a flag to the challenge"""

    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )
        return

    try:
        config = get_chall_config(_cwd)
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            f"An error occurred while getting the challenge config: {e}", style="red"
        )
        return

    ...


@app.command("hint")
def add_hint(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
):
    """Add a hint to the challenge"""

    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )
        return

    try:
        config = get_chall_config(_cwd)
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            f"An error occurred while getting the challenge config: {e}", style="red"
        )
        return

    ...


@app.command("service")
def add_service(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
):
    """Add a service to the challenge"""

    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )

    try:
        config = get_chall_config(_cwd)
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            f"An error occurred while getting the challenge config: {e}", style="red"
        )
        return

    ...
