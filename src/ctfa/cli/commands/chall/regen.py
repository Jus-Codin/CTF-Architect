from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter

from ctfa.cli.param_types import ResolvedExistingChallengeFolder


def command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    reformat_config: Annotated[bool, Parameter(name=["--reformat-config", "-c"])] = False,
):
    """Regenerate challenge README and config files.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to regenerate configs for
        reformat_config (bool, optional): Whether to reformat the challenge config file
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.challenge import Challenge

    chall = Challenge.load_folder(challenge_path)

    chall.save_readme()

    if reformat_config:
        chall.save_config()

    console.print(
        ":sparkles: Challenge files regenerated successfully! :sparkles:",
        style="ctfa.success",
    )
