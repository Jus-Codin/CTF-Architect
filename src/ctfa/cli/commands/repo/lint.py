from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter

from ctfa.cli.param_types import ResolvedExistingChallengeRepository
from ctfa.core.rules import SeverityLevel


def command(
    challenges: Annotated[
        list[str] | None, Parameter(name=["--challenge", "--challenges", "-c"], negative="", consume_multiple=True)
    ] = None,
    *,
    repository_path: Annotated[
        ResolvedExistingChallengeRepository, Parameter(name=["--repository", "-R"])
    ] = Path.cwd(),
    severity_level: Annotated[SeverityLevel, Parameter(name=["--level", "-l"])] = SeverityLevel.WARNING,
    ignore_rules: Annotated[list[str] | None, Parameter(name=["--ignore", "-i"])] = None,
    show_passed: Annotated[bool, Parameter(name=["--show-passed", "-P"])] = False,
    show_ignored: Annotated[bool, Parameter(name=["--show-ignored", "-I"])] = False,
    show_skipped: Annotated[bool, Parameter(name=["--show-skipped", "-S"])] = False,
):
    """Lint challenge folders in a challenge repository.

    By default, all challenge folders in the repository will be linted. You can specify
    specific challenges to lint using the --challenge/-c option.

    Args:
        challenges (list[str], optional): The specific challenges to lint
        repository_path (ResolvedExistingChallengeRepository, optional): The path to the challenge repository
        severity_level (SeverityLevel, optional): The minimum severity level to lint for
        ignore_rules (list[str], optional): The rule codes to ignore
        show_passed (bool, optional): Show output for rules that passed
        show_ignored (bool, optional): Show output for ignored rules
        show_skipped (bool, optional): Show output for skipped rules
    """
    from ctfa.cli.ui.components import ChallengeLintResultComponent, RepoLintResultComponent
    from ctfa.cli.ui.console import console
    from ctfa.core.exceptions import ConfigFileNotFoundError, InvalidChallengeRepositoryError
    from ctfa.core.lint import lint_challenge, lint_challenge_repository
    from ctfa.core.repository import ChallengeRepository

    try:
        repo = ChallengeRepository.load_repository(repository_path)
    except (InvalidChallengeRepositoryError, ConfigFileNotFoundError):
        console.print(
            f"Could not find the Repository Config file at {repository_path}. Are you sure this is the right directory?",
            style="ctfa.error",
        )
        return

    if challenges is None:
        results = lint_challenge_repository(repository_path, level=severity_level, ignore_rules=ignore_rules)

        console.print(
            RepoLintResultComponent(
                results,
                show_passed=show_passed,
                show_ignored=show_ignored,
                show_skipped=show_skipped,
            )
        )
    else:
        # Check if all challenges exist
        _challenge_paths = []

        for challenge_name in challenges:
            challenge_folder = repo.find_challenge_folder(challenge_name, validate=False)

            if challenge_folder is None:
                console.print(
                    f"Could not find challenge folder for challenge '{challenge_name}'. Please check the challenge name and try again.",
                    style="ctfa.error",
                )
                return

            _challenge_paths.append(challenge_folder)

        for challenge_path in _challenge_paths:
            result = lint_challenge(
                challenge_path, ctf_config=repo.ctf_config, level=severity_level, ignore_rules=ignore_rules
            )

            console.print(
                ChallengeLintResultComponent(
                    challenge_path,
                    result,
                    show_passed=show_passed,
                    show_ignored=show_ignored,
                    show_skipped=show_skipped,
                )
            )
            console.print()  # Spacing
