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
    """Update the stats for a challenge repository.

    Args:
        repository_path (ResolvedExistingChallengeRepository, optional): The path to the challenge repository to update stats for
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.exceptions import InvalidChallengeRepositoryError
    from ctfa.core.repository import ChallengeRepository

    try:
        repo = ChallengeRepository.load_repository(repository_path)
    except InvalidChallengeRepositoryError:
        console.print(
            f"Could not find a valid challenge repository at {repository_path}. Are you sure this is the right directory?",
            style="ctfa.error",
        )
        return

    repo.save_all_readmes()

    console.print(
        ":sparkles: Repository stats updated successfully! :sparkles:",
        style="ctfa.success",
    )
