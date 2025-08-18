"""Challenge and Repository initialization."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, TypedDict

from ctf_architect.core.challenge import write_chall_config, write_chall_readme
from ctf_architect.models.challenge import ChallengeConfig, Flag, Hint, Service


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
    target_dir: str | Path | None = None,
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
    if target_dir is not None:
        if isinstance(target_dir, str):
            target_dir = Path(target_dir)

        if target_dir.exists():
            if target_dir.is_file():
                raise IsADirectoryError(f'"{target_dir}" is a file.')
            elif any(target_dir.iterdir()):
                raise NotADirectoryError(f'"{target_dir}" is not empty.')
        else:
            target_dir.mkdir(parents=True, exist_ok=True)

    _flags = [Flag.model_validate(flag) for flag in flags]

    if hints is None:
        _hints = None
    else:
        _hints = [Hint.model_validate(hint) for hint in hints]

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        if dist_files is not None:
            (temp_path / "dist").mkdir()

            _files = []
            for file in dist_files:
                if isinstance(file, Path):
                    if not file.exists():
                        raise FileNotFoundError(f'File "{file}" does not exist.')

                    if not file.is_file():
                        raise IsADirectoryError(f'"{file}" is a directory.')

                    shutil.copy(file, temp_path / "dist")
                    _files.append((temp_path / "dist" / file.name).relative_to(temp_path))
                else:
                    # TODO: Validate the URL
                    _files.append(file)
        else:
            _files = None

        if source_files is not None:
            (temp_path / "src").mkdir()

            for file in source_files:
                if not file.exists():
                    raise FileNotFoundError(f'File "{file}" does not exist.')

                if file.is_file():
                    shutil.copy(file, temp_path / "src")
                else:
                    shutil.copytree(file, temp_path / "src" / file.name)

        (temp_path / "solution").mkdir()

        if solution_files is None:
            (temp_path / "solution" / "writeup.md").touch()
        else:
            create_writeup_md = True

            for file in solution_files:
                if not file.exists():
                    raise FileNotFoundError(f'File "{file}" does not exist.')

                if file.is_file():
                    shutil.copy(file, temp_path / "solution")
                else:
                    shutil.copytree(file, temp_path / "solution" / file.name)

                if file.name == "writeup.md":
                    create_writeup_md = False

            if create_writeup_md:
                (temp_path / "solution" / "writeup.md").touch()

        if services is not None:
            (temp_path / "service").mkdir()

            _services = []
            for service in services:
                _service = Service.model_validate(service)

                if not _service.path.exists():
                    raise FileNotFoundError(f'Service folder "{_service.path}" does not exist.')

                if not _service.path.is_dir():
                    raise NotADirectoryError(f'"{_service.path}" is not a directory.')

                shutil.copytree(_service.path, temp_path / "service" / _service.path.name)
                _service.path = (temp_path / "service" / _service.path.name).relative_to(temp_path)

                _services.append(_service)
        else:
            _services = None

        kwargs = {
            "author": author,
            "category": category,
            "description": description,
            "difficulty": difficulty,
            "name": name,
            "files": _files,
            "requirements": requirements,
            "extras": extras,
            "flags": _flags,
            "hints": _hints,
            "services": _services,
        }

        if folder_name is not None:
            kwargs["folder_name"] = folder_name

        chall = ChallengeConfig.model_validate(kwargs)

        write_chall_config(temp_path, chall)
        write_chall_readme(temp_path, chall)

        if target_dir is None:
            target_dir = Path(chall.folder_name)
            # Ensure directory exists
            target_dir.mkdir(parents=True, exist_ok=True)

        for file in temp_path.iterdir():
            shutil.move(file, target_dir / file.name)
