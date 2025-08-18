"""Challenge and Repository initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from ctf_architect.core.challenge import Challenge
from ctf_architect.models.challenge import ChallengeConfig


class FlagDict(TypedDict):
    flag: str
    regex: bool
    case_insensitive: bool


class HintDict(TypedDict):
    cost: int
    content: str
    requirements: list[int] | None


class ServiceDict(TypedDict):
    name: str
    path: Path
    port: int
    ports: list[int]
    type: Literal["web", "tcp", "ssh", "secret", "internal"]
    extras: dict[str, str | int | float | bool] | None


def init_chall(
    target_dir: str | Path,
    author: str,
    category: str,
    description: str,
    difficulty: str,
    name: str,
    flags: list[FlagDict],
    folder_name: str | None = None,
    dist_files: list[str | Path] | None = None,
    source_files: list[Path] | None = None,
    solution_files: list[Path] | None = None,
    requirements: list[str] | None = None,
    extras: dict[str, str | int | float | bool] | None = None,
    hints: list[HintDict] | None = None,
    services: list[ServiceDict] | None = None,
):
    """Initialize a new challenge.

    Args:
        target_dir (str | Path): The target directory to create the challenge in.
        author (str): The author of the challenge.
        category (str): The category of the challenge.
        description (str): The description of the challenge.
        difficulty (str): The difficulty of the challenge.
        name (str): The name of the challenge.
        flags (list[FlagDict]): The list of flags for the challenge.
        folder_name (str | None, optional): The folder name for the challenge. Defaults to None.
        dist_files (list[str | Path] | None, optional): The list of files for the challenge. If a string is provided, it will be interpreted as a URL. Defaults to None.
        source_files (list[Path] | None, optional): The list of source files for the challenge. Defaults to None.
        solution_files (list[Path] | None, optional): The list of solution files for the challenge. Defaults to None.
        requirements (list[str] | None, optional): The list of requirements needed to unlock the challenge. Defaults to None.
        extras (dict[str, str | int | float | bool] | None, optional): The extra fields for the challenge. Defaults to None.
        hints (list[HintDict] | None, optional): The list of hints for the challenge. Defaults to None.
        services (list[ServiceDict] | None, optional): The list of services for the challenge. Defaults to None.
    """
    kwargs = {
        "author": author,
        "category": category,
        "description": description,
        "difficulty": difficulty,
        "name": name,
        "files": dist_files,
        "requirements": requirements,
        "extras": extras,
        "flags": flags,
        "hints": hints,
        "services": services,
    }

    if folder_name is not None:
        kwargs["folder_name"] = folder_name

    extra_files = []

    if source_files is not None:
        for file in source_files:
            if not file.exists():
                raise FileNotFoundError(f'Source file "{file}" does not exist.')

            if file.is_file():
                extra_files.append((file, Path("src") / file.name))
            else:
                extra_files.append((file, Path("src")))

    if solution_files is not None:
        for file in solution_files:
            if not file.exists():
                raise FileNotFoundError(f'Solution file "{file}" does not exist.')

            if file.is_file():
                extra_files.append((file, Path("solution") / file.name))
            else:
                extra_files.append((file, Path("solution")))

    if not extra_files:
        extra_files = None

    chall_config = ChallengeConfig.model_validate(kwargs)

    chall = Challenge.new(target_dir, challenge_config=chall_config, extra_files=extra_files)

    if solution_files is None:
        (chall.path / "solution" / "writeup.md").touch()
