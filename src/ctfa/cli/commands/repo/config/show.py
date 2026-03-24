from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter

from ctfa.cli.param_types import ResolvedExistingChallengeRepository


def command(
    repository_path: Annotated[
        ResolvedExistingChallengeRepository, Parameter(name=["--repository", "-R"])
    ] = Path.cwd(),
):
    """Show the configuration of a challenge repository.

    Args:
        repository_path (ResolvedExistingChallengeRepository, optional): The path to the challenge repository
    """
    from ctfa.cli.ui.components import CTFConfigComponent
    from ctfa.cli.ui.console import console
    from ctfa.core.exceptions import ConfigFileNotFoundError, InvalidChallengeRepositoryError
    from ctfa.core.repository import ChallengeRepository

    try:
        repo = ChallengeRepository.load_repository(repository_path)
    except (InvalidChallengeRepositoryError, ConfigFileNotFoundError):
        console.print(
            f"Could not find the Repository config file at {repository_path}. Are you sure this is the right directory?",
            style="ctfa.error",
        )
        return

    console.print(CTFConfigComponent(repo.ctf_config))
