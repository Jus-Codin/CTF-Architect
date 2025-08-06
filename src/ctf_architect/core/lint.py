"""Linter to validate CTF challenges."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, StrEnum
from functools import total_ordering
from pathlib import Path
from traceback import format_exception_only

from ctf_architect.core.repo import Repo
from ctf_architect.core.rules import RULES
from ctf_architect.models.ctf_config import CTFConfig


@total_ordering
class SeverityLevel(Enum):
    """Severity level of a rule."""

    INFO = 0
    """Just for informational purposes"""
    WARNING = 1
    """Challenge will be able to be loaded, but may have issues"""
    ERROR = 2
    """Challenge will be unable to be loaded, but other rules can be checked"""
    FATAL = 3
    """Challenge will be unable to be loaded, non-fatal rules cannot be checked"""

    def __lt__(self, other: SeverityLevel) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class CheckStatus(StrEnum):
    """Status of a check."""

    PASSED = "passed"
    """Check passed."""
    IGNORED = "ignored"
    """Check was explicitly ignored."""
    SKIPPED = "skipped"
    """Check was unable to be performed."""
    FAILED = "failed"
    """Check failed."""
    ERROR = "error"
    """Check had an unexpected error."""


class CheckResult:
    """Represents the result of a rule check.

    Attributes:
        status (CheckStatus): The status of the check.
        code (str): The code of the check.
        level (SeverityLevel): The severity level of the check.
        message (str, optional): The message of the check. Defaults to None.
    """

    def __init__(self, status: CheckStatus, code: str, level: SeverityLevel, message: str | None = None):
        self.status = status
        self.code = code
        self.level = level
        self.message = message


class LintResult:
    """Represents the result of linting a challenge.

    Attributes:
        challenge_path (Path): The path to the challenge directory.
        passed (list[CheckResult]): List of checks that passed.
        ignored (list[CheckResult]): List of checks that were ignored.
        skipped (list[CheckResult]): List of checks that were skipped.
        failed (list[CheckResult]): List of checks that failed.
        errors (list[CheckResult]): List of checks that had errors.
    """

    def __init__(
        self,
        challenge_path: Path,
        passed: list[CheckResult],
        ignored: list[CheckResult],
        skipped: list[CheckResult],
        failed: list[CheckResult],
        errors: list[CheckResult],
    ):
        self.challenge_path = challenge_path
        self.passed = passed
        self.ignored = ignored
        self.skipped = skipped
        self.failed = failed
        self.errors = errors


class Rule:
    """Represents a lint rule.

    Attributes:
        code (str): The code of the rule.
        func (Callable): The function that implements the rule.
        message (str, optional): The message of the rule. Defaults to None.
        requires_ctf_config (bool): Whether the rule requires a CTF config. Defaults to False.
        repo_only (bool): Whether the rule is only applicable to repositories. Defaults to False.
    """

    def __init__(
        self,
        code: str,
        func: Callable,
        message: str | None = None,
        requires_ctf_config: bool = False,
        repo_only: bool = False,
    ):
        self.code = code
        self.func = func
        self.message = message
        self.requires_ctf_config = requires_ctf_config
        self.repo_only = repo_only

        self.__doc__ = func.__doc__

    def check(self, challenge_path: Path, ctf_config: CTFConfig | None = None) -> CheckResult:
        if ctf_config is None and self.requires_ctf_config:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=self.code,
                level=self.level,
                message="CTF config required for this check",
            )

        args = [challenge_path]  # type: list[Any]
        if ctf_config is not None and self.requires_ctf_config:
            args.append(ctf_config)

        try:
            result = self.func(*args)
        except Exception as e:
            return CheckResult(
                status=CheckStatus.ERROR,
                code=self.code,
                level=self.level,
                message="Error running check: " + "".join(format_exception_only(e)).strip(),
            )

        if isinstance(result, str):
            return CheckResult(
                status=CheckStatus.FAILED,
                code=self.code,
                level=self.level,
                message=result,
            )
        elif result is False:
            return CheckResult(
                status=CheckStatus.FAILED,
                code=self.code,
                level=self.level,
                message=self.message,
            )
        elif result is True:
            return CheckResult(
                status=CheckStatus.PASSED,
                code=self.code,
                level=self.level,
                message=None,
            )
        else:
            return result


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


def lint_challenge_repo(
    repo_path: Path | str,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore: list[str] | None = None,
) -> dict[str, dict[str, LintResult]]:
    """Lint all challenges in a repository.

    Args:
        repo_path (Path | str): The path to the repository.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore (list[str], optional): The list of rules to ignore. Defaults to None.

    Returns:
        dict[str, dict[str, LintResult]]: A dictionary mapping category names to dictionaries of challenge folder names and their lint results.
    """
    repo = Repo.from_path(repo_path)

    linter = Linter(repo.ctf_config, level, ignore)

    results = {}

    for category in repo.ctf_config.categories:
        results[category] = {}

        for challenge_path in repo.walk_chall_folders(category, skip_invalid=True):
            results[category][challenge_path.name] = linter.lint(challenge_path)

    return results
