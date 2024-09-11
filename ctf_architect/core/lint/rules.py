"""
Lint rules for challenges in CTF-Architect
"""

from __future__ import annotations

from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import Callable

from ctf_architect.core.challenge import find_challenge, get_chall_config
from ctf_architect.core.models import CTFConfig


@total_ordering
class SeverityLevel(Enum):
    # Just for informational purposes
    INFO = 0
    # Challenge will be able to be loaded, but may have issues
    WARNING = 1
    # Challenge will be unable to be loaded, but other rules can be checked
    ERROR = 2
    # Challenge will be unable to be loaded, non-fatal rules cannot be checked
    FATAL = 3

    def __lt__(self, other: SeverityLevel) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Rule:
    def __init__(
        self,
        code: str,
        level: SeverityLevel,
        check: Callable[[Path, CTFConfig | None], bool | str],
        message: str | None = None,
    ):
        self.code = code
        self.level = level

        # This is the function that will be called to check the rule
        self.check = check

        self.message = message


RULES: list[Rule] = []
RULES_DICT: dict[str, Rule] = {}


def get_rule(code: str) -> Rule:
    return RULES_DICT[code]


def add_rule(rule: Rule):
    if rule.code in RULES_DICT:
        raise ValueError(f"Rule with code {rule.code} already exists")

    RULES_DICT[rule.code] = rule
    RULES.append(rule)


def rule(code: str, level: SeverityLevel, message: str | None = None):
    def decorator(f: Callable[[Path, CTFConfig | None], bool | str]) -> Rule:
        rule = Rule(code=code, level=level, check=f, message=message)
        add_rule(rule)
        return rule

    return decorator


# File Structure Rules
@rule(
    "F000",
    level=SeverityLevel.FATAL,
    message="chall.toml file is missing",
)
def F000(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    return (challenge_path / "chall.toml").exists()


@rule(
    "F001",
    level=SeverityLevel.ERROR,
    message="Solution folder is missing or empty",
)
def F001(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    return (challenge_path / "solution").exists() and any(
        (challenge_path / "solution").iterdir()
    )


@rule(
    "F002",
    level=SeverityLevel.WARNING,
    message="No writeup.md file with content in solution folder found",
)
def F002(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    writeup = challenge_path / "solution" / "writeup.md"
    return (
        not writeup.exists() or writeup.read_bytes().strip()
    )  # Use bytes to avoid decoding errors


@rule(
    "F004",
    level=SeverityLevel.ERROR,
    message="README.md file must exist and have content",
)
def F004(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    readme = challenge_path / "README.md"
    return (
        readme.exists() and len(readme.read_bytes().strip()) > 0
    )  # Use bytes to avoid decoding errors


# Challenge Configuration Rules
@rule(
    "C000",
    level=SeverityLevel.FATAL,
)
def C000(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    try:
        get_chall_config(challenge_path)
    except Exception as e:
        return "Failed to load chall.toml file: " + str(e)

    return True


@rule(
    "C001",
    level=SeverityLevel.ERROR,
)
def C001(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    if ctf_config is None:
        # CTF config is not loaded, so we can't check this rule
        return True

    challenge = get_chall_config(challenge_path)

    if challenge.category not in ctf_config.categories:
        return f'Invalid category "{challenge.category}" in chall.toml file'
    else:
        return True


@rule(
    "C002",
    level=SeverityLevel.ERROR,
)
def C002(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    if ctf_config is None:
        # CTF config is not loaded, so we can't check this rule
        return True

    challenge = get_chall_config(challenge_path)

    if challenge.difficulty not in [d.name for d in ctf_config.difficulties]:
        return f'Invalid difficulty "{challenge.difficulty}" in chall.toml file'
    else:
        return True


@rule(
    "C003",
    level=SeverityLevel.ERROR,
)
def C003(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    if ctf_config is None:
        # CTF config is not loaded, so we can't check this rule
        return True

    challenge = get_chall_config(challenge_path)

    missing_extras = []

    for extra in ctf_config.extras:
        if extra not in challenge.extras:
            missing_extras.append(extra)

    if missing_extras:
        return f'Missing extras in chall.toml file: {", ".join(missing_extras)}'
    else:
        return True


@rule(
    "C004",
    level=SeverityLevel.ERROR,
    message="File specified in chall.toml not found or is absolute path",
)
def C004(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    challenge = get_chall_config(challenge_path)

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

    return result if result else True


@rule(
    "C005",
    level=SeverityLevel.WARNING,
    message="Challenge has no flags",
)
def C005(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    challenge = get_chall_config(challenge_path)

    return challenge.flags is None or len(challenge.flags) == 0


@rule(
    "C006",
    level=SeverityLevel.INFO,
    message="Challenge only has a description and no files or services",
)
def C006(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool:
    challenge = get_chall_config(challenge_path)

    return not (challenge.files or challenge.services)


@rule(
    "C007",
    level=SeverityLevel.ERROR,
    message="Challenge folder name and name in chall.toml do not match",
)
def C007(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    challenge = get_chall_config(challenge_path)

    if challenge_path.name != challenge.folder_name:
        return f'Folder name does not match name in chall.toml (expected "{challenge.folder_name}", got "{challenge_path.name}")'

    return True


@rule(
    "C008",
    level=SeverityLevel.ERROR,
    message="Challenge requirement not found in Challenge Repository",
)
def C008(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    if ctf_config is None:
        # CTF config is not loaded, so we can't check this rule
        return True

    challenge = get_chall_config(challenge_path)

    missing_reqs = []

    if challenge.requirements is not None:
        for req in challenge.requirements:
            if not find_challenge(req):
                missing_reqs.append(req)

    if missing_reqs:
        return f"Requirements in chall.toml file could not be found or loaded: {', '.join(missing_reqs)}"
    else:
        return True


# Service Configuration Rules
@rule(
    "S000",
    level=SeverityLevel.ERROR,
    message="Path specified in service does not exist",
)
def S000(challenge_path: Path, ctf_config: CTFConfig | None = None) -> bool | str:
    challenge = get_chall_config(challenge_path)

    if challenge.services is None:
        return True

    missing_paths = {}
    absolute_paths = {}

    for service in challenge.services:
        if service.path.is_absolute():
            absolute_paths[service.name] = service.path
        if not (challenge_path / service.path).exists():
            missing_paths[service.name] = service.path

    result = ""

    if absolute_paths:
        s = "Paths specified in services are absolute paths:\n"
        for name, path in absolute_paths.items():
            s += f"  - {name}: {path}\n"
        result += s

    if missing_paths:
        s = "Paths specified in services do not exist:\n"
        for name, path in missing_paths.items():
            s += f"  - {name}: {path}\n"
        result += s

    return result if result else True
