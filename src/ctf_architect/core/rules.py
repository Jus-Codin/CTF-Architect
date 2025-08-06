"""Lint rules for challenges in CTF Architect."""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import Enum, StrEnum
from functools import total_ordering
from pathlib import Path
from traceback import format_exception_only
from typing import Literal

from ctf_architect.constants import CHALLENGE_CONFIG_FILE
from ctf_architect.core.challenge import Challenge, load_chall_config
from ctf_architect.core.exceptions import DuplicateRuleCodeError
from ctf_architect.core.repo import Repo
from ctf_architect.models.ctf_config import CTFConfig

RULES: list[Rule] = []
RULES_DICT: dict[str, Rule] = {}


def get_rule(code: str) -> Rule:
    return RULES_DICT[code]


def add_rule(rule: Rule):
    if rule.code in RULES_DICT:
        raise DuplicateRuleCodeError(f"Rule with code {rule.code} already exists")
    RULES.append(rule)
    RULES_DICT[rule.code] = rule


def rule(
    code: str,
    level: SeverityLevel,
    message: str | None = None,
    requires_ctf_config: bool = False,
    repo_only: bool = False,
):
    def decorator(
        f: Callable[[CheckContext], bool | str | CheckResult],
    ) -> Rule:
        rule = Rule(
            code=code,
            level=level,
            func=f,
            message=message,
            requires_ctf_config=requires_ctf_config,
            repo_only=repo_only,
        )
        add_rule(rule)
        return rule

    return decorator


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


class CheckContext:
    """Context for a check.

    Attributes:
        challenge_path (Path): The path to the challenge directory.
        ctf_config (CTFConfig | None): The CTF configuration, if available.
        repo (Repo | None): The repository, if available.
    """

    def __init__(self, challenge_path: Path, ctf_config: CTFConfig | None = None, repo: Repo | None = None):
        if ctf_config is None and repo is not None:
            ctf_config = repo.ctf_config

        self.challenge_path = challenge_path
        self.ctf_config = ctf_config
        self.repo = repo


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


class Rule:
    """Represents a lint rule.

    Attributes:
        code (str): The code of the rule.
        level (SeverityLevel): The severity level of the rule.
        func (Callable): The function that implements the rule.
        message (str, optional): The message of the rule. Defaults to None.
        requires_ctf_config (bool): Whether the rule requires a CTF config. Defaults to False.
        repo_only (bool): Whether the rule is only applicable to challenges in repositories. Defaults to False.
    """

    def __init__(
        self,
        code: str,
        level: SeverityLevel,
        func: Callable[[CheckContext], bool | str | CheckResult],
        message: str | None = None,
        requires_ctf_config: bool = False,
        repo_only: bool = False,
    ):
        self.code = code
        self.level = level
        self.func = func
        self.message = message
        self.requires_ctf_config = requires_ctf_config
        self.repo_only = repo_only

        self.__doc__ = func.__doc__

    def check(self, context: CheckContext) -> CheckResult:
        try:
            result = self.func(context)
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


# FILE STRUCTURE RULES
@rule(
    "F000",
    level=SeverityLevel.FATAL,
    message=f"{CHALLENGE_CONFIG_FILE} is missing",
)
def F000(ctx: CheckContext) -> bool:
    """Check if the challenge directory contains a challenge config file."""
    return (ctx.challenge_path / CHALLENGE_CONFIG_FILE).exists()


@rule(
    "F001",
    level=SeverityLevel.WARNING,
    message="Solution folder is missing or empty",
)
def F001(ctx: CheckContext) -> bool:
    """Check if the challenge directory contains a solution folder."""
    return (ctx.challenge_path / "solution").exists() and any((ctx.challenge_path / "solution").iterdir())


@rule(
    "F002",
    level=SeverityLevel.WARNING,
    message="No writeup.md with content in solution folder found",
)
def F002(ctx: CheckContext) -> bool:
    """Check if the solution folder contains a writeup.md file with content."""
    writeup = ctx.challenge_path / "solution" / "writeup.md"
    return not writeup.exists() or len(writeup.read_bytes().strip()) > 0


@rule(
    "F003",
    level=SeverityLevel.ERROR,
    message="README.md file must exist and have content",
)
def F003(ctx: CheckContext) -> bool:
    """Check if the challenge directory contains a README.md file with content."""
    readme = ctx.challenge_path / "README.md"
    return readme.exists() and len(readme.read_bytes().strip()) > 0


# CHALLENGE CONFIG RULES
@rule(
    "C000",
    level=SeverityLevel.FATAL,
)
def C000(ctx: CheckContext) -> Literal[True] | str:
    """Check if the challenge config file can be loaded."""
    try:
        Challenge.load_config(ctx.challenge_path)
    except Exception as e:
        return f"Failed to load {CHALLENGE_CONFIG_FILE} file: " + "".join(format_exception_only(e)).strip()

    return True


@rule(
    "C001",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C001(ctx: CheckContext) -> Literal[True] | str:
    """Check if the challenge category is valid."""
    challenge = load_chall_config(ctx.challenge_path)

    if challenge.category not in ctx.ctf_config.categories:
        return f'Invalid category "{challenge.category}" in {CHALLENGE_CONFIG_FILE} file'
    else:
        return True


@rule(
    "C002",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C002(ctx: CheckContext) -> Literal[True] | str:
    """Check if the challenge difficulty is valid."""
    challenge = load_chall_config(ctx.challenge_path)

    if challenge.difficulty not in ctx.ctf_config.difficulties:
        return f'Invalid difficulty "{challenge.difficulty}" in {CHALLENGE_CONFIG_FILE} file'
    else:
        return True


@rule(
    "C003",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C003(ctx: CheckContext) -> Literal[True] | str:
    """Check for missing extras in the challenge config."""
    challenge = Challenge.load_config(ctx.challenge_path)

    missing_extras = []

    config_extras = ctx.ctf_config.extras or []
    challenge_extras = challenge.extras or {}

    for extra in config_extras:
        if extra.name not in challenge_extras and extra.required:
            missing_extras.append(extra)

    if missing_extras:
        result = f"Missing required extras in {CHALLENGE_CONFIG_FILE} file:\n"
        for extra in missing_extras:
            result += f"  - {extra.name} ({extra.description})\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C004",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C004(ctx: CheckContext) -> Literal[True] | str:
    """Check for extra extras in the challenge config."""
    challenge = Challenge.load_config(ctx.challenge_path)

    # What is this variable naming...
    extra_extras = []

    config_extras = [e.name for e in ctx.ctf_config.extras] if ctx.ctf_config.extras else []
    challenge_extras = challenge.extras or {}

    for extra in challenge_extras:
        if extra not in config_extras:
            extra_extras.append(extra)

    if extra_extras:
        result = f"Extra extras in {CHALLENGE_CONFIG_FILE} file:\n"
        for extra in extra_extras:
            result += f"  - {extra}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C005",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C005(ctx: CheckContext) -> Literal[True] | str:
    """Check for incorrect extra types in the challenge config."""
    type_mapping = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
    }

    challenge = Challenge.load_config(ctx.challenge_path)

    incorrect_extras = []

    config_extras = ctx.ctf_config.extras or []
    challenge_extras = challenge.extras or {}

    for extra in config_extras:
        if extra.name in challenge_extras and extra.type in type_mapping:
            if not isinstance(challenge_extras[extra.name], type_mapping[extra.type]):
                incorrect_extras.append(extra)

    if incorrect_extras:
        result = f"Incorrect extra types in {CHALLENGE_CONFIG_FILE} file:\n"
        for extra in incorrect_extras:
            result += f"  - {extra.name} (expected {extra.type}, got {type(challenge_extras[extra.name])})\n"
        return result.rstrip()
    else:
        return True


# TODO: Maybe split into two rules
@rule(
    "C006",
    level=SeverityLevel.WARNING,
    message="File specified in chall.toml not found or is absolute path",
)
def C006(ctx: CheckContext) -> Literal[True] | str:
    challenge = Challenge.load_config(ctx.challenge_path)

    if challenge.files is None:
        return True

    missing_files = []
    absolute_files = []

    for file in challenge.files:
        if isinstance(file, Path):
            if file.is_absolute():
                absolute_files.append(file)
            if not (ctx.challenge_path / file).exists():
                missing_files.append(file)

    result = ""

    if absolute_files:
        s = "Files specified in chall.toml are absolute paths:\n"
        for file in absolute_files:
            s += f"  - {file}\n"
        result += s

    if missing_files:
        s = "Files specified in chall.toml do not exist:\n"
        for file in missing_files:
            s += f"  - {file}\n"
        result += s

    return result.rstrip() if result else True


@rule(
    "C007",
    level=SeverityLevel.WARNING,
    message="Challenge has no flags",
)
def C007(ctx: CheckContext) -> bool:
    """Check if the challenge has flags."""
    challenge = Challenge.load_config(ctx.challenge_path)

    return challenge.flags is not None and len(challenge.flags) > 0


@rule(
    "C008",
    level=SeverityLevel.WARNING,
    message="Challenge flag does not match the format specified in the CTF config",
    requires_ctf_config=True,
)
def C008(ctx: CheckContext) -> Literal[True] | str | CheckResult:
    """Check if the challenge flag matches the format specified in the CTF config."""
    challenge = Challenge.load_config(ctx.challenge_path)

    if ctx.ctf_config.flag_format is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C008",
            level=SeverityLevel.WARNING,
            message="No flag format specified in CTF config",
        )

    if challenge.flags is None or len(challenge.flags) == 0:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C008",
            level=SeverityLevel.WARNING,
            message="No flags in challenge",
        )

    invalid_flags = []

    for flag in challenge.flags:
        if not re.match(ctx.ctf_config.flag_format, flag.flag):
            invalid_flags.append(flag.flag)

    if invalid_flags:
        result = f'Flags do not match the flag format "{ctx.ctf_config.flag_format}":\n'
        for flag in invalid_flags:
            result += f"  - {flag}\n"
        return result.rstrip()
    else:
        return True


# Sometimes people forget to add files or services to the challenge
# This rule is here to flag that
@rule(
    "C009",
    level=SeverityLevel.WARNING,
    message="Challenge only has a description and no files or services",
)
def C009(ctx: CheckContext) -> bool:
    """Check if the challenge only has a description and no files or services."""
    challenge = Challenge.load_config(ctx.challenge_path)

    return challenge.files is not None or challenge.services is not None


@rule(
    "C010",
    level=SeverityLevel.ERROR,
    message="Challenge folder name and name in chall.toml do not match",
)
def C010(ctx: CheckContext) -> Literal[True] | str:
    """Check if the challenge folder name matches the name in chall.toml."""
    challenge = Challenge.load_config(ctx.challenge_path)

    if ctx.challenge_path.name != challenge.folder_name:
        return f'Folder name does not match name in chall.toml (expected "{challenge.folder_name}", got "{ctx.challenge_path.name}")'

    return True


@rule(
    "C011",
    level=SeverityLevel.ERROR,
    message="Challenge requirement not found in Challenge Repository",
    repo_only=True,
)
def C011(ctx: CheckContext) -> Literal[True] | str | CheckResult:
    """Check if the challenge requirements are valid."""
    challenge = Challenge.load_config(ctx.challenge_path)

    missing_requirements = []

    if challenge.requirements is not None:
        for req in challenge.requirements:
            if not ctx.repo.find_challenge(req):
                missing_requirements.append(req)

    if missing_requirements:
        result = "Requirements in chall.toml file could not be found or loaded:\n"
        for req in missing_requirements:
            result += f"  - {req}\n"
        return result.rstrip()
    else:
        return True


# SERVICE RULES
@rule(
    "S000",
    level=SeverityLevel.FATAL,
    message="Path specified for service does not exist or is an absolute path",
)
def S000(ctx: CheckContext) -> Literal[True] | str | CheckResult:
    challenge = Challenge.load_config(ctx.challenge_path)

    if challenge.services is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="S000",
            level=SeverityLevel.FATAL,
            message="No services defined in challenge",
        )

    missing_paths = []
    absolute_paths = []

    for service in challenge.services:
        if service.path.is_absolute():
            absolute_paths.append(service.path)
        if not (ctx.challenge_path / service.path).exists():
            missing_paths.append(service.path)

    result = ""

    if absolute_paths:
        s = "Paths specified for services are absolute paths:\n"
        for path in absolute_paths:
            s += f"  - {path}\n"
        result += s

    if missing_paths:
        s = "Paths specified for services do not exist:\n"
        for path in missing_paths:
            s += f"  - {path}\n"
        result += s

    return result.rstrip() if result else True
