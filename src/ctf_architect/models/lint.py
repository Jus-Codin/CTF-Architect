from __future__ import annotations

from collections.abc import Callable
from enum import Enum, StrEnum
from functools import total_ordering
from pathlib import Path
from traceback import format_exception_only
from typing import Any

from ctf_architect.models.base import Model
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


class CheckResult(Model):
    """Represents the result of a check.

    Attributes:
        status (CheckStatus): The status of the check.
        code (str): The code of the check.
        level (SeverityLevel): The severity level of the check.
        message (str, optional): The message of the check. Defaults to None.
    """

    status: CheckStatus
    code: str
    level: SeverityLevel
    message: str | None = None


class Rule(Model):
    code: str
    level: SeverityLevel
    func: Callable[[Path], bool | str | CheckResult] | Callable[[Path, CTFConfig], bool | str | CheckResult]
    message: str | None = None
    requires_ctf_config: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.__doc__ = self.func.__doc__

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


class LintResult(Model):
    """Represents the result of a lint check.

    Attributes:
        challenge_path (Path): The path to the challenge.
        passed (list[CheckResult]): Checks that passed.
        ignored (list[CheckResult]): Checks that were ignored.
        skipped (list[CheckResult]): Checks that were skipped.
        failed (list[CheckResult]): Checks that failed.
        errors (list[CheckResult]): Checks that had errors
    """

    challenge_path: Path
    passed: list[CheckResult]
    ignored: list[CheckResult]
    skipped: list[CheckResult]
    failed: list[CheckResult]
    errors: list[CheckResult]
