"""Lint rules for challenges in CTF Architect."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from traceback import format_exception_only
from typing import Literal

from ctf_architect.constants import CHALLENGE_CONFIG_FILE
from ctf_architect.core.challenge import load_chall_config
from ctf_architect.core.exceptions import DuplicateRuleCodeError
from ctf_architect.core.repo import find_challenge, is_challenge_repo
from ctf_architect.models.ctf_config import CTFConfig
from ctf_architect.models.lint import CheckResult, CheckStatus, Rule, SeverityLevel

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
):
    def decorator(
        f: Callable[[Path], bool | str | CheckResult] | Callable[[Path, CTFConfig], bool | str | CheckResult],
    ) -> Rule:
        rule = Rule(
            code=code,
            level=level,
            func=f,
            message=message,
            requires_ctf_config=requires_ctf_config,
        )
        add_rule(rule)
        return rule

    return decorator


# FILE STRUCTURE RULES
@rule(
    "F000",
    level=SeverityLevel.FATAL,
    message=f"{CHALLENGE_CONFIG_FILE} is missing",
)
def F000(challenge_path: Path) -> bool:
    """Check if the challenge directory contains a {CHALLENGE_CONFIG_FILE} file."""
    return (challenge_path / "chall.toml").exists()


@rule(
    "F001",
    level=SeverityLevel.WARNING,
    message="Solution folder is missing or empty",
)
def F001(challenge_path: Path) -> bool:
    """Check if the challenge directory contains a solution folder."""
    return (challenge_path / "solution").exists() and any((challenge_path / "solution").iterdir())


@rule(
    "F002",
    level=SeverityLevel.WARNING,
    message="No writeup.md with content in solution folder found",
)
def F002(challenge_path: Path) -> bool:
    """Check if the solution folder contains a writeup.md file with content."""
    writeup = challenge_path / "solution" / "writeup.md"
    return not writeup.exists() or len(writeup.read_bytes().strip()) > 0


@rule(
    "F003",
    level=SeverityLevel.ERROR,
    message="README.md file must exist and have content",
)
def F003(challenge_path: Path) -> bool:
    """Check if the challenge directory contains a README.md file with content."""
    readme = challenge_path / "README.md"
    return readme.exists() and len(readme.read_bytes().strip()) > 0


# CHALLENGE CONFIG RULES
@rule(
    "C000",
    level=SeverityLevel.FATAL,
)
def C000(challenge_path: Path) -> Literal[True] | str:
    """Check if the challenge config file can be loaded."""
    try:
        load_chall_config(challenge_path)
    except Exception as e:
        return f"Failed to load {CHALLENGE_CONFIG_FILE} file: " + "".join(format_exception_only(e)).strip()

    return True


@rule(
    "C001",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C001(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check if the challenge category is valid."""
    challenge = load_chall_config(challenge_path)

    if challenge.category not in ctf_config.categories:
        return f'Invalid category "{challenge.category}" in {CHALLENGE_CONFIG_FILE} file'
    else:
        return True


@rule(
    "C002",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C002(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check if the challenge difficulty is valid."""
    challenge = load_chall_config(challenge_path)

    if challenge.difficulty not in ctf_config.difficulties:
        return f'Invalid difficulty "{challenge.difficulty}" in {CHALLENGE_CONFIG_FILE} file'
    else:
        return True


@rule(
    "C003",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C003(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for missing extras in the challenge config."""
    challenge = load_chall_config(challenge_path)

    missing_extras = []

    config_extras = ctf_config.extras or []
    challenge_extras = challenge.extras or {}

    for extra in config_extras:
        if extra.name not in challenge_extras:
            missing_extras.append(extra)

    if missing_extras:
        result = f"Missing extras in {CHALLENGE_CONFIG_FILE} file:\n"
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
def C004(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for extra extras in the challenge config."""
    challenge = load_chall_config(challenge_path)

    # What is this variable naming...
    extra_extras = []

    config_extras = [e.name for e in ctf_config.extras] if ctf_config.extras else []
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
def C005(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for incorrect extra types in the challenge config."""
    type_mapping = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
    }

    challenge = load_chall_config(challenge_path)

    incorrect_extras = []

    config_extras = ctf_config.extras or []
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
def C006(challenge_path: Path) -> Literal[True] | str:
    challenge = load_chall_config(challenge_path)

    if challenge.files is None:
        return True

    missing_files = []
    absolute_files = []

    for file in challenge.files:
        if isinstance(file, Path):
            if file.is_absolute():
                absolute_files.append(file)
            if not (challenge_path / file).exists():
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
def C007(challenge_path: Path) -> bool:
    """Check if the challenge has flags."""
    challenge = load_chall_config(challenge_path)

    return challenge.flags is not None and len(challenge.flags) > 0


@rule(
    "C008",
    level=SeverityLevel.WARNING,
    message="Challenge flag does not match the format specified in the CTF config",
    requires_ctf_config=True,
)
def C008(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str | CheckResult:
    """Check if the challenge flag matches the format specified in the CTF config."""
    challenge = load_chall_config(challenge_path)

    if ctf_config.flag_format is None:
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
        if not re.match(ctf_config.flag_format, flag.flag):
            invalid_flags.append(flag.flag)

    if invalid_flags:
        result = f'Flags do not match the flag format "{ctf_config.flag_format}":\n'
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
def C009(challenge_path: Path) -> bool:
    """Check if the challenge only has a description and no files or services."""
    challenge = load_chall_config(challenge_path)

    return challenge.files is not None or challenge.services is not None


@rule(
    "C010",
    level=SeverityLevel.ERROR,
    message="Challenge folder name and name in chall.toml do not match",
)
def C010(challenge_path: Path) -> Literal[True] | str:
    challenge = load_chall_config(challenge_path)

    if challenge_path.name != challenge.folder_name:
        return f'Folder name does not match name in chall.toml (expected "{challenge.folder_name}", got "{challenge_path.name}")'

    return True


@rule(
    "C011",
    level=SeverityLevel.ERROR,
    message="Challenge requirement not found in Challenge Repository",
)
def C011(challenge_path: Path) -> Literal[True] | str | CheckResult:
    # Check if this is run in a Challenge Repository
    if not is_challenge_repo():
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C011",
            level=SeverityLevel.ERROR,
            message="Not in a Challenge Repository",
        )

    challenge = load_chall_config(challenge_path)

    missing_requirements = []

    if challenge.requirements is not None:
        for req in challenge.requirements:
            if not find_challenge(req):
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
def S000(challenge_path: Path) -> Literal[True] | str | CheckResult:
    challenge = load_chall_config(challenge_path)

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
        if not (challenge_path / service.path).exists():
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
