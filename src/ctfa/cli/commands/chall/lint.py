from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ResolvedExistingFile
from questionary import confirm

from ctfa.cli.param_types import ResolvedExistingChallengeFolder
from ctfa.core.rules import SeverityLevel


def command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    ctf_config_file: Annotated[ResolvedExistingFile | None, Parameter(name=["--config", "-c"])] = None,
    *,
    severity_level: Annotated[SeverityLevel, Parameter(name=["--level", "-l"])] = SeverityLevel.WARNING,
    ignore_rules: Annotated[list[str] | None, Parameter(name=["--ignore", "-i"])] = None,
    show_passed: Annotated[bool, Parameter(name=["--show-passed", "-P"])] = False,
    show_ignored: Annotated[bool, Parameter(name=["--show-ignored", "-I"])] = False,
    show_skipped: Annotated[bool, Parameter(name=["--show-skipped", "-S"])] = False,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Lint a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to lint
        ctf_config_file (ResolvedExistingFile, optional): The path to the CTF Config to validate the challenge against
        severity_level (SeverityLevel, optional): The minimum severity level to lint for
        ignore_rules (list[str], optional): The rule codes to ignore
        show_passed (bool, optional): Show output for rules that passed
        show_ignored (bool, optional): Show output for ignored rules
        show_skipped (bool, optional): Show output for skipped rules
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.components import ChallengeLintResultComponent
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.flows import ask_ctf_config
    from ctfa.core.lint import lint_challenge
    from ctfa.core.repository import ChallengeRepository

    if ctf_config_file is None:
        if not no_interactive and confirm("Would you like to select a CTF config file?").ask():
            ctf_config = ask_ctf_config(gui=True)
        else:
            ctf_config = None
    else:
        ctf_config = ChallengeRepository.load_config_file(ctf_config_file)

    result = lint_challenge(challenge_path, ctf_config, severity_level, ignore_rules)

    console.print(
        ChallengeLintResultComponent(
            challenge_path,
            result,
            show_passed=show_passed,
            show_ignored=show_ignored,
            show_skipped=show_skipped,
        )
    )
