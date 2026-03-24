from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ResolvedExistingFile

from ctfa.cli.param_types import ResolvedNonChallengeFolder


def command(
    location: Annotated[ResolvedNonChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    ctf_config_file: Annotated[ResolvedExistingFile | None, Parameter(name=["--config", "-c"])] = None,
    new: Annotated[bool, Parameter(name=["--new", "-n"])] = False,
    no_src: Annotated[bool, Parameter(name=["--no-src"], negative="")] = False,
    no_writeup: Annotated[bool, Parameter(name=["--no-writeup"], negative="")] = False,
):
    """Initialise a new challenge folder.

    Args:
        location (ResolvedNonChallengeFolder, optional): The location to create the challenge folder in
        ctf_config_file (ResolvedExistingFile | None, optional): The path to the CTF configuration file
        new (bool, optional): Create the challenge as a subfolder
        no_src (bool, optional): Do not create the src/ folder
        no_writeup (bool, optional): Do not create the solution/writeup.md file
    """
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.flows import ask_challenge_details, ask_ctf_config
    from ctfa.core.challenge import Challenge

    if not new:
        folder_name = location.name
    else:
        folder_name = None

    extra_files = {
        "src": {},
        "solution": {
            "writeup.md": "",
        },
    }

    if no_src:
        extra_files.pop("src")

    if no_writeup:
        extra_files.pop("solution")

    if ctf_config_file is None:
        from ctfa.cli.ui.flows import ask_ctf_config

        ctf_config = ask_ctf_config(gui=True)

        if ctf_config is None:
            console.print("Aborting...", style="ctfa.error")
            return

        # Add spacing
        console.print()
    else:
        from ctfa.core.repository import ChallengeRepository

        ctf_config = ChallengeRepository.load_config_file(ctf_config_file)

    challenge_config = ask_challenge_details(ctf_config, folder_name=folder_name)

    if challenge_config is None:
        console.print("Aborting...", style="ctfa.error")
        return

    challenge = Challenge.package(challenge_config, location, extra_files=extra_files, as_subfolder=new)

    console.print(f"Challenge '{challenge_config.name}' initialised at {challenge.location}", style="ctfa.success")
