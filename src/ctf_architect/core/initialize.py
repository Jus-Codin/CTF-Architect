"""Challenge and Repository initialization."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, TypedDict

from ctf_architect.core.challenge import save_chall_config, save_chall_readme
from ctf_architect.core.repo import load_repo_config, save_repo_config
from ctf_architect.core.stats import update_category_readme, update_root_readme
from ctf_architect.models.challenge import Challenge, Flag, Hint, Service
from ctf_architect.models.ctf_config import CTFConfig, ExtraField


class ExtraFieldDict(TypedDict):
    """Extra field dictionary type.

    Attributes:
        name (str): The name of the extra field.
        description (str): The description of the extra field.
        prompt (str): The prompt of the extra field.
        required (bool): Specifies whether the extra field is required.
        type (Literal["string", "integer", "float", "boolean"]): The type of the extra field.
    """

    name: str
    description: str
    prompt: str
    required: bool
    type: Literal["string", "integer", "float", "boolean"]


def init_repo_no_config(
    name: str,
    categories: list[str],
    difficulties: list[str],
    flag_format: str | None = None,
    starting_port: int | None = None,
    extras: list[ExtraFieldDict] | None = None,
    config_only: bool = False,
) -> None:
    """Initialize a new challenge repository in the current directory.

    Args:
        name (str): The name of the CTF.
        categories (list[str]): The list of categories for the CTF.
        difficulties (list[str]): The list of difficulties for the CTF.
        flag_format (str | None, optional): The flag format for the CTF. Defaults to None.
        starting_port (int | None, optional): The starting port for services in the CTF. Defaults to None.
        extras (list[ExtraFieldDict] | None, optional): The list of extra fields for challenges in the CTF. Defaults to None.
        config_only (bool, optional): Whether to only save the config file. Defaults to False.
    """
    extra_fields = None
    if extras is not None:
        extra_fields = [ExtraField.model_validate(extra) for extra in extras]

    ctf_config = CTFConfig(
        name=name,
        categories=categories,
        difficulties=difficulties,
        flag_format=flag_format,
        starting_port=starting_port,
        extras=extra_fields,
    )

    save_repo_config(ctf_config)

    if not config_only:
        # Create the challenge folder
        Path("challenges").mkdir(exist_ok=True)

        # Create the folders for each category
        for category in categories:
            Path(f"challenges/{category.lower()}").mkdir(exist_ok=True)

        # Update the root README
        update_root_readme()

        # Update the README for each category
        for category in categories:
            update_category_readme(category)


def init_repo_from_config() -> None:
    """Initialize a new challenge repository from a config file."""
    config = load_repo_config()

    # Create the challenge folder
    Path("challenges").mkdir(exist_ok=True)

    # Create the folders for each category
    for category in config.categories:
        Path(f"challenges/{category.lower()}").mkdir(exist_ok=True)

    # Update the root README
    update_root_readme()

    # Update the README for each category
    for category in config.categories:
        update_category_readme(category)


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
            target_dir.mkdir()

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

                if not file.is_file():
                    raise IsADirectoryError(f'"{file}" is a directory.')

                shutil.copy(file, temp_path / "src")

        (temp_path / "solution").mkdir()

        if solution_files is None:
            (temp_path / "solution" / "writeup.md").touch()
        else:
            create_writeup_md = True

            for file in solution_files:
                if not file.exists():
                    raise FileNotFoundError(f'File "{file}" does not exist.')

                if not file.is_file():
                    raise IsADirectoryError(f'"{file}" is a directory.')

                shutil.copy(file, temp_path / "solution")

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

        chall = Challenge.model_validate(kwargs)

        save_chall_config(temp_path, chall)
        save_chall_readme(temp_path, chall)

        if target_dir is None:
            target_dir = Path(chall.folder_name)

        shutil.move(temp_path, target_dir)
