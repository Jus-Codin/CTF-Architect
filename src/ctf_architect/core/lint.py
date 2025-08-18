"""Linter to validate CTF challenges."""

from __future__ import annotations

from pathlib import Path

from ctf_architect.core.repo import Repo
from ctf_architect.core.rules import RULES, CheckContext, CheckResult, CheckStatus, Rule, SeverityLevel
from ctf_architect.models.ctf_config import CTFConfig


class LintResult:
    """Represents the result of linting a challenge.

    Attributes:
        challenge_path (Path): The path to the challenge directory.
        passed (list[CheckResult], optional): List of checks that passed.
        ignored (list[CheckResult], optional): List of checks that were ignored.
        skipped (list[CheckResult], optional): List of checks that were skipped.
        failed (list[CheckResult], optional): List of checks that failed.
        errors (list[CheckResult], optional): List of checks that had errors.
    """

    def __init__(
        self,
        challenge_path: Path,
        passed: list[CheckResult] | None = None,
        ignored: list[CheckResult] | None = None,
        skipped: list[CheckResult] | None = None,
        failed: list[CheckResult] | None = None,
        errors: list[CheckResult] | None = None,
    ):
        self.challenge_path = challenge_path
        self.passed = passed or []
        self.ignored = ignored or []
        self.skipped = skipped or []
        self.failed = failed or []
        self.errors = errors or []


class Linter:
    """Linter to validate CTF challenges.

    Warning: The linter allows `ctf_config` to be a different config from the one in the `repo`.
             However, doing so may lead to unexpected results. In general, rules that require a repo should use the repo's CTF config.

    Attributes:
        ctf_config (CTFConfig | None): The CTF configuration, if available.
        repo (Repo | None): The repository, if available.
        level (SeverityLevel): The severity level to lint at.
        ignore (list[str]): The list of rules to ignore.
    """

    def __init__(
        self,
        ctf_config: CTFConfig | None = None,
        repo: Repo | None = None,
        level: SeverityLevel = SeverityLevel.INFO,
        ignore: list[str] | None = None,
    ):
        self.ctf_config = ctf_config
        self.repo = repo
        self.level = level
        self.ignore = ignore or []

        # Check if repo is initialized
        if repo is not None and not repo.initialized:
            raise RuntimeError("Cannot lint challenges in an uninitialized repository")

    def get_context(self, challenge_path: Path) -> CheckContext:
        """Get the context for a check."""
        return CheckContext(
            challenge_path=challenge_path,
            ctf_config=self.ctf_config,
            repo=self.repo,
        )

    def process_rule(self, challenge_path: Path, rule: Rule) -> CheckResult:
        """Process a rule for a challenge."""
        context = self.get_context(challenge_path)

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

        if rule.requires_ctf_config and context.ctf_config is None:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="CTF config required for this check",
            )

        if rule.repo_only and context.repo is None:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="Check is applicable only to challenges in a repository",
            )

        return rule.check(context)

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
    linter = Linter(ctf_config, repo=None, level=level, ignore=ignore)
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

    linter = Linter(repo.ctf_config, repo=repo, level=level, ignore=ignore)

    results = {}

    for category in repo.ctf_config.categories:
        results[category] = {}

        for challenge_path in repo.walk_chall_folders(category, skip_invalid=True):
            results[category][challenge_path.name] = linter.lint(challenge_path)

    return results
