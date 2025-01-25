"""Linter to validate CTF challenges."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, overload

from ctf_architect.core.challenge import is_challenge_folder
from ctf_architect.core.repo import load_repo_config
from ctf_architect.core.rules import RULES
from ctf_architect.models.ctf_config import CTFConfig
from ctf_architect.models.lint import (
    CheckResult,
    CheckStatus,
    LintResult,
    Rule,
    SeverityLevel,
)


class Linter:
    """Linter to validate CTF challenges."""

    def __init__(
        self,
        ctf_config: CTFConfig | None = None,
        level: SeverityLevel = SeverityLevel.INFO,
        ignore: list[str] | None = None,
    ):
        self.ctf_config = ctf_config
        self.level = level
        self.ignore = ignore or []

    def process_rule(self, challenge_path: Path, rule: Rule) -> CheckResult:
        """Process a rule for a challenge."""
        if rule.level < self.level:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="Rule level too low",
            )

        if rule.code in self.ignore:
            return CheckResult(
                status=CheckStatus.IGNORED,
                code=rule.code,
                level=rule.level,
                message="Rule in ignore list",
            )

        return rule.check(challenge_path, self.ctf_config)

    def lint(self, challenge_path: Path) -> LintResult:
        """Lint a challenge directory."""
        result = LintResult(
            challenge_path=challenge_path,
            passed=[],
            ignored=[],
            skipped=[],
            failed=[],
            errors=[],
        )

        attr_map = {
            CheckStatus.PASSED: result.passed,
            CheckStatus.IGNORED: result.ignored,
            CheckStatus.SKIPPED: result.skipped,
            CheckStatus.FAILED: result.failed,
            CheckStatus.ERROR: result.errors,
        }

        fatal_rules = [rule for rule in RULES if rule.level == SeverityLevel.FATAL]

        # Process fatal rules first
        for rule in fatal_rules:
            check_result = self.process_rule(challenge_path, rule)
            attr_map[check_result.status].append(check_result)

        if result.failed or result.errors:
            return result

        non_fatal_rules = [rule for rule in RULES if rule.level != SeverityLevel.FATAL]

        for rule in non_fatal_rules:
            check_result = self.process_rule(challenge_path, rule)
            attr_map[check_result.status].append(check_result)

        return result


def lint_challenge(
    challenge_path: Path,
    ctf_config: CTFConfig | None = None,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore: list[str] | None = None,
) -> LintResult:
    """Lint a challenge directory.

    Args:
        challenge_path (Path): The path to the challenge directory.
        ctf_config (CTFConfig, optional): The CTF configuration. Defaults to None.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore (list[str], optional): The list of rules to ignore. Defaults to None.

    Returns:
        LintResult: The result of the linting.
    """
    linter = Linter(ctf_config, level, ignore)
    return linter.lint(challenge_path)


@overload
def lint_challenge_repo(
    *,
    by_category: Literal[False],
    repo_path: Path | str | None = None,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore: list[str] | None = None,
) -> dict[str, LintResult]: ...


@overload
def lint_challenge_repo(
    *,
    by_category: Literal[True],
    repo_path: Path | str | None = None,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore: list[str] | None = None,
) -> dict[str, dict[str, LintResult]]: ...


def lint_challenge_repo(
    repo_path: Path | str | None = None,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore: list[str] | None = None,
    by_category: bool = False,
) -> dict[str, LintResult] | dict[str, dict[str, LintResult]]:
    """Lint a challenge repository.

    Args:
        repo_path (Path | str | None, optional): The path to the repository. If not specified, the current directory is used. Defaults to None.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore (list[str], optional): The list of rules to ignore. Defaults to None.
        by_category (bool, optional): Whether to return the results by category. Defaults to False.

    Returns:
        dict[str, LintResult] | dict[str, dict[str, LintResult]]: The result of the linting.
    """
    if repo_path is None:
        repo_path = Path.cwd()
    elif isinstance(repo_path, str):
        repo_path = Path(repo_path)

    ctf_config = load_repo_config(repo_path)

    linter = Linter(ctf_config, level, ignore)

    results = {}

    for category in ctf_config.categories:
        if by_category:
            results[category] = {}

        category_path = repo_path / "challenges" / category.lower()

        for challenge_path in category_path.iterdir():
            if challenge_path.is_dir() and is_challenge_folder(challenge_path):
                if by_category:
                    results[category][challenge_path.name] = linter.lint(challenge_path)
                else:
                    results[challenge_path.name] = linter.lint(challenge_path)

    return results
