from __future__ import annotations

from pathlib import Path
from typing import Any

from ctfa.core.repository import ChallengeRepository
from ctfa.core.rules import RULES, CheckResult, CheckStatus, Rule, SeverityLevel
from ctfa.models.ctf_config import CTFConfig


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
    """Runs lint rules on challenges.

    Attributes:
        ctf_config (CTFConfig, optional): The CTF configuration, if available.
        repo (ChallengeRepository, optional): The repository, if available.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore_rules (list[str], optional): The list of rules to ignore.
    """

    def __init__(
        self,
        ctf_config: CTFConfig | None = None,
        repo: ChallengeRepository | None = None,
        level: SeverityLevel = SeverityLevel.INFO,
        ignore_rules: list[str] | None = None,
    ):
        self.ctf_config = ctf_config
        self.repo = repo
        self.level = level
        self.ignore_rules = ignore_rules or []

    def process_rule(self, challenge_path: Path, rule: Rule[Any, Any]) -> CheckResult:
        """Process a single rule on a challenge.

        Args:
            challenge_path (Path): The path to the challenge directory.
            rule (Rule): The rule to process.

        Returns:
            CheckResult: The result of the check.
        """
        if rule.level < self.level:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="Rule level is lower than the linter's level",
            )

        if rule.code in self.ignore_rules:
            return CheckResult(
                status=CheckStatus.IGNORED,
                code=rule.code,
                level=rule.level,
                message="Rule is in ignore list",
            )

        if rule.requires_ctf_config and self.ctf_config is None:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="CTF config is required for this rule",
            )

        if rule.repository_only and self.repo is None:
            return CheckResult(
                status=CheckStatus.SKIPPED,
                code=rule.code,
                level=rule.level,
                message="Rule is applicable only to challenges in a repository",
            )

        # Build arguments for the rule check
        check_args = []
        check_args.append(challenge_path)
        if rule.requires_ctf_config:
            check_args.append(self.ctf_config)
        if rule.repository_only:
            check_args.append(self.repo)

        return rule.check(*check_args)

    def lint(self, challenge_path: Path) -> LintResult:
        """Run all rule checks on a challenge folder."""
        result = LintResult(challenge_path=challenge_path)

        status_to_list_map = {
            CheckStatus.PASSED: result.passed,
            CheckStatus.IGNORED: result.ignored,
            CheckStatus.SKIPPED: result.skipped,
            CheckStatus.FAILED: result.failed,
            CheckStatus.ERROR: result.errors,
        }

        # Process fatal rules first
        for rule in RULES.get_fatal():
            check_result = self.process_rule(challenge_path, rule)
            status_to_list_map[check_result.status].append(check_result)

            if result.failed or result.errors:
                return result  # Stop processing if fatal rule fails or errors

        # Process non-fatal rules
        for rule in RULES.get_non_fatal():
            check_result = self.process_rule(challenge_path, rule)
            status_to_list_map[check_result.status].append(check_result)

        return result


# ----------------------------------------------------------------
# Public API
# ----------------------------------------------------------------


def lint_challenge(
    challenge_path: Path | str,
    ctf_config: CTFConfig | None = None,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore_rules: list[str] | None = None,
) -> LintResult:
    """Lint a challenge folder.

    Args:
        challenge_path (Path): The path to the challenge directory.
        ctf_config (CTFConfig, optional): The CTF configuration, if available.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore_rules (list[str], optional): The list of rules to ignore.

    Returns:
        LintResult: The result of linting the challenge.
    """
    if isinstance(challenge_path, str):
        challenge_path = Path(challenge_path)

    linter = Linter(
        ctf_config=ctf_config,
        repo=None,
        level=level,
        ignore_rules=ignore_rules,
    )
    return linter.lint(challenge_path)


def lint_challenge_repository(
    repository_path: Path | str,
    level: SeverityLevel = SeverityLevel.INFO,
    ignore_rules: list[str] | None = None,
) -> dict[str, dict[str, LintResult]]:
    """Lint all challenges in a repository.

    Args:
        repository_path (Path | str): The path to the challenge repository.
        level (SeverityLevel, optional): The severity level to lint at. Defaults to SeverityLevel.INFO.
        ignore_rules (list[str], optional): The list of rules to ignore.

    Returns:
        dict[str, dict[str, LintResult]]: A tree-like structure mapping category names to dictionaries of challenge folder names and their lint results.
    """
    if isinstance(repository_path, str):
        repository_path = Path(repository_path)

    repo = ChallengeRepository.load_repository(repository_path)

    linter = Linter(
        ctf_config=repo.ctf_config,
        repo=repo,
        level=level,
        ignore_rules=ignore_rules,
    )

    results: dict[str, dict[str, LintResult]] = {}

    for category in repo.ctf_config.categories:
        results[category] = {}

        for challenge_path in repo.walk_challenge_folders(
            category,
            skip_invalid=True,
        ):
            results[category][challenge_path.name] = linter.lint(challenge_path)

    return results
