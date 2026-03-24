from __future__ import annotations

import re
from collections.abc import Callable
from enum import Enum, StrEnum
from functools import total_ordering
from pathlib import Path
from traceback import format_exception_only
from typing import Any, Generic, Literal, ParamSpec, TypeAlias, TypeVar, overload

from ctfa.constants import CHALLENGE_CONFIG_FILE
from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.models.ctf_config import CTFConfig


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


RuleReturn: TypeAlias = "bool | str | CheckResult"

P = ParamSpec("P")
R = TypeVar("R", bound=RuleReturn)


class Rule(Generic[P, R]):
    def __init__(
        self,
        code: str,
        level: SeverityLevel,
        func: Callable[P, R],
        message: str | None = None,
        requires_ctf_config: bool = False,
        repository_only: bool = False,
    ):
        self.code = code
        self.level = level
        self.func = func
        self.message = message
        self.requires_ctf_config = requires_ctf_config
        self.repository_only = repository_only

        self.__doc__ = func.__doc__

    def check(self, *args: P.args, **kwargs: P.kwargs) -> CheckResult:
        try:
            result = self.func(*args, **kwargs)
        except Exception as e:
            return CheckResult(
                status=CheckStatus.ERROR,
                code=self.code,
                level=self.level,
                message="Error running check: " + "".join(format_exception_only(e)).strip(),
            )
        if isinstance(result, CheckResult):
            return result
        elif isinstance(result, str):
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
            return CheckResult(
                status=CheckStatus.ERROR,
                code=self.code,
                level=self.level,
                message="Invalid return type from check",
            )


class RuleRegistry:
    def __init__(self):
        self._rules_list: list[Rule[Any, Any]] = []
        self._rules_map: dict[str, Rule[Any, Any]] = {}

    def add(self, rule: Rule[Any, Any]) -> None:
        """Add a rule to the registry."""
        if rule.code in self._rules_map:
            raise ValueError(f"Rule with code {rule.code} already exists in registry")
        self._rules_list.append(rule)
        self._rules_map[rule.code] = rule

    def get_all(self) -> list[Rule[Any, Any]]:
        """Get all rules in the registry."""
        return self._rules_list.copy()

    def get_fatal(self) -> list[Rule[Any, Any]]:
        """Get all fatal rules in the registry."""
        return [rule for rule in self._rules_list if rule.level == SeverityLevel.FATAL]

    def get_non_fatal(self) -> list[Rule[Any, Any]]:
        """Get all non-fatal rules in the registry."""
        return [rule for rule in self._rules_list if rule.level != SeverityLevel.FATAL]

    def __iter__(self):
        return iter(self._rules_list)


RULES = RuleRegistry()


# Rule without ctf config or repo requirement
@overload
def rule(  # pyright: ignore[reportOverlappingOverload]
    code: str,
    *,
    level: SeverityLevel,
    message: str | None = ...,
    requires_ctf_config: Literal[False] = ...,
    repository_only: Literal[False] = ...,
) -> Callable[[Callable[[Path], R]], Rule[[Path], R]]: ...


# Rule with ctf config requirement
@overload
def rule(
    code: str,
    *,
    level: SeverityLevel,
    message: str | None = ...,
    requires_ctf_config: Literal[True] = True,
) -> Callable[[Callable[[Path, CTFConfig], R]], Rule[[Path, CTFConfig], R]]: ...


# Rule with repo requirement
@overload
def rule(
    code: str,
    *,
    level: SeverityLevel,
    message: str | None = ...,
    repository_only: Literal[True] = True,
) -> Callable[[Callable[[Path, ChallengeRepository], R]], Rule[[Path, ChallengeRepository], R]]: ...


# Rule with both ctf config and repo requirement
@overload
def rule(  # pyright: ignore[reportOverlappingOverload]
    code: str,
    *,
    level: SeverityLevel,
    message: str | None = ...,
    requires_ctf_config: Literal[True] = True,
    repository_only: Literal[True] = True,
) -> Callable[
    [Callable[[Path, CTFConfig, ChallengeRepository], R]], Rule[[Path, CTFConfig, ChallengeRepository], R]
]: ...


def rule(
    code: str,
    *,
    level: SeverityLevel,
    message: str | None = None,
    requires_ctf_config: bool = False,
    repository_only: bool = False,
) -> Callable[[Callable[..., R]], Rule[..., R]]:
    """Decorator to define a rule.

    Args:
        code (str): The code of the rule.
        level (SeverityLevel): The severity level of the rule.
        message (str | None, optional): The message of the rule. Defaults to None.
        requires_ctf_config (bool, optional): Whether the rule requires a CTF config. Defaults to False.
        repository_only (bool, optional): Whether the rule requires a repository. Defaults to False.
    """

    def decorator(func: Callable[..., R]) -> Rule[..., R]:
        r = Rule(
            code=code,
            level=level,
            func=func,
            message=message,
            requires_ctf_config=requires_ctf_config,
            repository_only=repository_only,
        )
        RULES.add(r)
        return r

    return decorator


# ----------------------------------------------------------------
# FILE STRUCTURE RULES
# ----------------------------------------------------------------
@rule(
    "F000",
    level=SeverityLevel.FATAL,
    message=f"{CHALLENGE_CONFIG_FILE} is missing",
)
def F000(challenge_path: Path) -> bool:
    """Check that the challenge configuration file exists."""
    config_path = challenge_path / CHALLENGE_CONFIG_FILE
    return config_path.exists() and config_path.is_file()


@rule(
    "F001",
    level=SeverityLevel.WARNING,
    message="Solution folder is missing or empty",
)
def F001(challenge_path: Path) -> bool:
    """Check if the challenge folder contains a non-empty 'solution' directory."""
    solution_path = challenge_path / "solution"
    return solution_path.exists() and any(solution_path.iterdir())


@rule(
    "F002",
    level=SeverityLevel.WARNING,
    message="No writeup.md file found in solution folder",
)
def F002(challenge_path: Path) -> bool:
    """Check if the solution folder contains a writeup.md file."""
    writeup_path = challenge_path / "solution" / "writeup.md"
    return not writeup_path.exists() or len(writeup_path.read_bytes().strip()) > 0


@rule(
    "F003",
    level=SeverityLevel.ERROR,
    message="README.md file must exist and have content",
)
def F003(challenge_path: Path) -> bool:
    """Check if the challenge folder contains a README.md file with content."""
    readme_path = challenge_path / "README.md"
    return readme_path.exists() and len(readme_path.read_bytes().strip()) > 0


# ----------------------------------------------------------------
# CHALLENGE CONFIG RULES
# ----------------------------------------------------------------
@rule(
    "C000",
    level=SeverityLevel.FATAL,
)
def C000(challenge_path: Path) -> Literal[True] | str:
    """Check if the challenge config can be loaded."""
    try:
        Challenge.load_config_file(challenge_path)
    except Exception as e:
        return f"Failed to load {CHALLENGE_CONFIG_FILE} file: " + "".join(format_exception_only(e)).strip()

    return True


@rule(
    "C001",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C001(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check if the challenge config has a valid category."""
    challenge_config = Challenge.load_config_file(challenge_path)
    if challenge_config.category not in ctf_config.categories:
        return f'Invalid category "{challenge_config.category}"in {CHALLENGE_CONFIG_FILE}'
    else:
        return True


@rule(
    "C002",
    level=SeverityLevel.ERROR,
    requires_ctf_config=True,
)
def C002(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check if the challenge has a valid difficulty."""
    challenge_config = Challenge.load_config_file(challenge_path)
    if challenge_config.difficulty not in ctf_config.difficulties:
        return f'Invalid difficulty "{challenge_config.difficulty}" in {CHALLENGE_CONFIG_FILE}'
    else:
        return True


@rule(
    "C003",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C003(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for missing required extra labels in challenge config."""
    challenge_config = Challenge.load_config_file(challenge_path)

    missing_labels = []

    repo_labels = ctf_config.extra_labels or []
    challenge_labels = challenge_config.extra_labels or {}

    for label in repo_labels:
        if label.required and label.name not in challenge_labels:
            missing_labels.append(label)

    if missing_labels:
        result = f"Missing required extra labels in {CHALLENGE_CONFIG_FILE}:\n"
        for label in missing_labels:
            result += f"  - {label.name} ({label.description})\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C004",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C004(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for extra labels in challenge config that are not defined in CTF config."""
    challenge_config = Challenge.load_config_file(challenge_path)

    undefined_labels = []

    repo_labels = ctf_config.extra_labels or []
    challenge_labels = challenge_config.extra_labels or {}

    repo_label_names = [label.name for label in repo_labels]

    for label_name in challenge_labels.keys():
        if label_name not in repo_label_names:
            undefined_labels.append(label_name)

    if undefined_labels:
        result = f"Undefined extra labels in {CHALLENGE_CONFIG_FILE}:\n"
        for label_name in undefined_labels:
            result += f"  - {label_name}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C005",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C005(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str:
    """Check for extra labels in challenge config that have invalid types."""
    type_mapping = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
    }

    challenge_config = Challenge.load_config_file(challenge_path)

    incorrect_labels = []

    repo_labels = ctf_config.extra_labels or []
    challenge_labels = challenge_config.extra_labels or {}

    repo_label_dict = {label.name: label for label in repo_labels}

    for label_name, label_value in challenge_labels.items():
        if label_name in repo_label_dict:
            expected_type_str = repo_label_dict[label_name].type
            expected_type = type_mapping.get(expected_type_str)
            if expected_type and not isinstance(label_value, expected_type):
                incorrect_labels.append((label_name, expected_type_str, type(label_value).__name__))

    if incorrect_labels:
        result = f"Extra labels with incorrect types in {CHALLENGE_CONFIG_FILE}:\n"
        for label_name, expected_type_str, actual_type_str in incorrect_labels:
            result += f"  - {label_name}: expected {expected_type_str}, got {actual_type_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C006",
    level=SeverityLevel.WARNING,
)
def C006(challenge_path: Path) -> Literal[True] | str:
    """Check if the static files specified in the challenge config exist."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.files is None:
        return True

    missing_files = []

    for file in challenge_config.files:
        if file.type == "static":
            if not file.path.is_absolute():
                file_path = challenge_path / file.path
            else:
                file_path = file.path

            if not file_path.exists() or not file_path.is_file():
                missing_files.append(str(file.path))

    if missing_files:
        result = f"Files specified in {CHALLENGE_CONFIG_FILE} are missing:\n"
        for file_path_str in missing_files:
            result += f"  - {file_path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C007",
    level=SeverityLevel.WARNING,
)
def C007(challenge_path: Path) -> Literal[True] | str:
    """Check if the staticfiles specified in the challenge config are not absolute paths."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.files is None:
        return True

    absolute_files = []

    for file in challenge_config.files:
        if file.type == "static":
            if file.path.is_absolute():
                absolute_files.append(str(file.path))

    if absolute_files:
        result = f"Static files in {CHALLENGE_CONFIG_FILE} should not use absolute paths:\n"
        for file_path_str in absolute_files:
            result += f"  - {file_path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C008",
    level=SeverityLevel.WARNING,
)
def C008(challenge_path: Path) -> Literal[True] | str:
    """Check if there are duplicate filenames in the challenge config files."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.files is None:
        return True

    filename_counts: dict[str, int] = {}

    for file in challenge_config.files:
        if file.type == "static":
            filename = file.path.name
        else:
            filename = str(file.url)
        filename_counts[filename] = filename_counts.get(filename, 0) + 1

    duplicate_filenames = [filename for filename, count in filename_counts.items() if count > 1]

    if duplicate_filenames:
        result = f"Duplicate filenames/URLs found in {CHALLENGE_CONFIG_FILE}:\n"
        for filename in duplicate_filenames:
            result += f"  - {filename}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C009",
    level=SeverityLevel.WARNING,
)
def C009(challenge_path: Path) -> Literal[True] | str:
    """Check if any static file paths are outside the challenge directory."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.files is None:
        return True

    outside_files = []

    for file in challenge_config.files:
        if file.type == "static":
            if not file.path.is_absolute():
                file_path = (challenge_path / file.path).resolve()
            else:
                file_path = file.path.resolve()

            try:
                file_path.relative_to(challenge_path.resolve())
            except ValueError:
                outside_files.append(str(file.path))

    if outside_files:
        result = f"Static files in {CHALLENGE_CONFIG_FILE} are outside the challenge directory:\n"
        for file_path_str in outside_files:
            result += f"  - {file_path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C010",
    level=SeverityLevel.WARNING,
    message="Challenge has no flags defined",
)
def C010(challenge_path: Path) -> bool:
    """Check if the challenge has at least one flag defined."""
    challenge_config = Challenge.load_config_file(challenge_path)
    return bool(challenge_config.flags and len(challenge_config.flags) > 0)


@rule(
    "C011",
    level=SeverityLevel.WARNING,
    requires_ctf_config=True,
)
def C011(challenge_path: Path, ctf_config: CTFConfig) -> Literal[True] | str | CheckResult:
    """Check if the challenge flags match the format specified in the CTF config."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if ctf_config.flag_format is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C011",
            level=SeverityLevel.WARNING,
            message="No flag format specified in CTF config",
        )

    try:
        pattern = re.compile(ctf_config.flag_format)
    except re.error as e:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C011",
            level=SeverityLevel.WARNING,
            message=f"Invalid flag format regex in CTF config: {e}",
        )

    if challenge_config.flags is None or len(challenge_config.flags) == 0:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="C011",
            level=SeverityLevel.WARNING,
            message="No flags defined in challenge config",
        )

    invalid_flags = []

    for flag in challenge_config.flags:
        # We only validate static flags here
        if flag.type == "static":
            if not pattern.fullmatch(flag.value):
                invalid_flags.append(flag.value)

    if invalid_flags:
        result = f'Flags do not match the required format "{ctf_config.flag_format}":\n'
        for flag_value in invalid_flags:
            result += f"  - {flag_value}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "C012",
    level=SeverityLevel.WARNING,
)
def C012(challenge_path: Path) -> Literal[True] | str:
    """Check if the challenge folder name matches the defined name in the challenge config."""
    challenge_config = Challenge.load_config_file(challenge_path)
    expected_name = challenge_config.folder_name
    actual_name = challenge_path.name

    if expected_name != actual_name:
        return f'Challenge folder name does not match name in {CHALLENGE_CONFIG_FILE} (expected "{expected_name}", got "{actual_name}")'
    else:
        return True


@rule(
    "C013",
    level=SeverityLevel.ERROR,
    repository_only=True,
)
def C013(challenge_path: Path, repo: ChallengeRepository) -> Literal[True] | str:
    """Check if the challenge requirements are valid."""
    challenge_config = Challenge.load_config_file(challenge_path)

    missing_requirements = []

    if challenge_config.requirements is not None:
        for req in challenge_config.requirements:
            if not repo.find_challenge(req):
                missing_requirements.append(req)

    if missing_requirements:
        result = f"Challenge requirements in {CHALLENGE_CONFIG_FILE} not found in repository:\n"
        for req in missing_requirements:
            result += f"  - {req}\n"
        return result.rstrip()
    else:
        return True


# ----------------------------------------------------------------
# SERVICE RULES
# ----------------------------------------------------------------
@rule(
    "S000",
    level=SeverityLevel.FATAL,
)
def S000(challenge_path: Path) -> Literal[True] | str | CheckResult:
    """Check if path specified for services exists."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.services is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="S000",
            level=SeverityLevel.FATAL,
            message="No services defined in challenge config",
        )

    missing_paths = []

    for service in challenge_config.services:
        if service.path.is_absolute():
            service_path = service.path
        else:
            service_path = challenge_path / service.path
        if not service_path.exists() or not service_path.is_dir():
            missing_paths.append(service.path)

    if missing_paths:
        result = f"Service paths specified in {CHALLENGE_CONFIG_FILE} are missing:\n"
        for path_str in missing_paths:
            result += f"  - {path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "S001",
    level=SeverityLevel.FATAL,
)
def S001(challenge_path: Path) -> Literal[True] | str | CheckResult:
    """Check if paths specified for services is not absolute."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.services is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="S001",
            level=SeverityLevel.FATAL,
            message="No services defined in challenge config",
        )

    absolute_paths = []

    for service in challenge_config.services:
        if service.path.is_absolute():
            absolute_paths.append(service.path)

    if absolute_paths:
        result = f"Service paths in {CHALLENGE_CONFIG_FILE} should not use absolute paths:\n"
        for path_str in absolute_paths:
            result += f"  - {path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "S002",
    level=SeverityLevel.ERROR,
)
def S002(challenge_path: Path) -> Literal[True] | str | CheckResult:
    """Check if service paths is within the challenge directory."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.services is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="S002",
            level=SeverityLevel.ERROR,
            message="No services defined in challenge config",
        )

    outside_paths = []

    for service in challenge_config.services:
        if not service.path.is_absolute():
            service_path = (challenge_path / service.path).resolve()
        else:
            service_path = service.path.resolve()

        try:
            service_path.relative_to(challenge_path.resolve())
        except ValueError:
            outside_paths.append(service.path)

    if outside_paths:
        result = f"Service paths in {CHALLENGE_CONFIG_FILE} are outside the challenge directory:\n"
        for path_str in outside_paths:
            result += f"  - {path_str}\n"
        return result.rstrip()
    else:
        return True


@rule(
    "S003",
    level=SeverityLevel.WARNING,
)
def S003(challenge_path: Path) -> Literal[True] | str | CheckResult:
    """Check if the service directories contain a Dockerfile."""
    challenge_config = Challenge.load_config_file(challenge_path)

    if challenge_config.services is None:
        return CheckResult(
            status=CheckStatus.SKIPPED,
            code="S003",
            level=SeverityLevel.WARNING,
            message="No services defined in challenge config",
        )

    missing_dockerfiles = []

    for service in challenge_config.services:
        if service.path.is_absolute():
            service_path = service.path
        else:
            service_path = challenge_path / service.path

        for file in service_path.iterdir():
            if file.name.lower() == "dockerfile" and file.is_file():
                break
        else:
            missing_dockerfiles.append(service.path)

    if missing_dockerfiles:
        result = "Services do not contain a Dockerfile:\n"
        for service_name in missing_dockerfiles:
            result += f"  - {service_name}\n"
        return result.rstrip()
    else:
        return True
