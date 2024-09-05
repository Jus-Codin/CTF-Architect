from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Generator

from pydantic import ValidationError
from tomlkit import load

from ctf_architect.core.config import load_config
from ctf_architect.core.constants import (
    CHALL_README_TEMPLATE,
    CHALLENGE_CONFIG_FILE,
    CTF_CONFIG_FILE,
)
from ctf_architect.core.models import Challenge, ChallengeFile


def is_challenge_folder(path: str | Path) -> bool:
    """
    Checks if the specified folder is a challenge folder.

    If it has a chall.toml file, it is considered a challenge folder.
    """
    for file in Path(path).iterdir():
        if file.name.lower() == CHALLENGE_CONFIG_FILE:
            return True

    return False


def is_challenge_repo() -> bool:
    """
    Checks if the current working directory is a challenge repo.

    A challenge repo is considered valid if it has a CTF config file and a challenges directory
    """
    return Path(CTF_CONFIG_FILE).exists() and Path("challenges").exists()


def walk_challenge_folders(category: str | None = None) -> Generator[Path]:
    """
    Walks through all challenge folders in the challenges directory.
    Can specify a category to only walk through challenges in that category.
    """
    config = load_config()

    challenges_path = Path("challenges")

    if category is not None:
        if category.lower() not in config.categories:
            raise ValueError(f"Category {category} not in CTF config")
        categories = [category.lower()]
    else:
        categories = config.categories

    for category in categories:
        if not (challenges_path / category).exists():
            continue
        for directory in (challenges_path / category).iterdir():
            if directory.is_dir():
                yield directory


def get_chall_config(path: str | Path) -> Challenge:
    if isinstance(path, str):
        path = Path(path)

    with (path / CHALLENGE_CONFIG_FILE).open("r", encoding="utf-8") as f:
        data = load(f)

    try:
        config_file = ChallengeFile.model_validate(data.unwrap())
    except ValidationError as e:
        raise ValueError(f"Invalid challenge config: {e}") from e

    challenge = config_file.challenge

    return challenge


def find_challenge(name: str) -> Challenge | None:
    """
    Tries to find a challenge with the given name.
    Returns the found challenge config
    """

    # Search Strategy:
    # 1. Search by the folder name, if match found, check challenge config file to verify
    # 2. Search every challenge config file for a name match

    # Get all possible challenge folders
    folders = list(walk_challenge_folders())

    searched = []

    folder_name = re.sub(r"[^a-zA-Z0-9-_ ]", "", name).strip()

    for folder in folders:
        if folder_name.lower() in folder.name.lower():
            searched.append(folder)
            try:
                challenge = get_chall_config(folder)
                if challenge.name.lower() == name.lower():
                    return challenge
            except Exception:
                pass

    for folder in folders:
        if folder in searched:
            continue
        try:
            challenge = get_chall_config(folder)
            if challenge.name.lower() == name.lower():
                return challenge
        except Exception:
            pass


def add_challenge(folder: str | Path, replace: bool = False) -> None:
    """
    Adds a challenge from the specified path to the challenges folder.

    If replace is True, will overwrite the challenge if it already exists.
    """
    config = load_config()

    if isinstance(folder, str):
        folder = Path(folder)

    if not folder.is_dir():
        raise ValueError(f'"{folder.absolute()}" is not a directory')

    challenge = get_chall_config(folder)

    # Check if the category exists
    # This is to prevent a challenge from being added to a category that doesn't exist
    if challenge.category not in config.categories:
        raise ValueError(f'Invalid category "{challenge.category}" in chall.toml file')

    # Check if path for the challenge already exists
    if challenge.repo_path.exists():
        # Check if te challenge in that path is the same name as the new challenge
        old_challenge = get_chall_config(challenge.repo_path)
        if old_challenge.name == challenge.name:
            if replace:
                remove_challenge(path=challenge.repo_path)
            else:
                raise FileExistsError(
                    f"Challenge with name {challenge.name} already exists"
                )
        else:
            # Folder name collision, throw error
            raise FileExistsError(
                "Another challenge is using the same folder name. Please resolve the conflict.\n"
                f"  Old Challenge: {old_challenge.name}\n"
                f"  New Challenge: {challenge.name}"
            )

    # Check if a challenge with the same name already exists
    # Honestly if the challenge is in another category, we can have the same name
    # but it's probably better practice to not have the same name
    elif (c := find_challenge(challenge.name)) is not None:
        if replace:
            remove_challenge(path=c.repo_path)
        else:
            raise FileExistsError(
                f"Challenge with name {challenge.name} already exists"
            )

    new_path = challenge.repo_path
    folder.rename(new_path)


def remove_challenge(name: str | None = None, path: Path | str | None = None):
    """
    Removes a challenge from the challenges folder.
    Can specify either the name or the path to the challenge folder.
    """

    if name is not None and path is not None:
        raise ValueError("Can only specify name or path, not both")

    if name is not None:
        challenge = find_challenge(name)
        if challenge is None:
            raise FileNotFoundError(f"Challenge with name {name} not found")
        path = challenge.repo_path
    elif path is not None:
        if isinstance(path, str):
            path = Path(path)
        if not path.is_dir():
            raise ValueError(f'"{path.absolute()}" is not a directory')
        # Safety check to make sure path is in the challenge repo
        if path.resolve().parent not in Path("challenges").resolve().iterdir():
            raise ValueError(f'"{path.absolute()}" is not in the CTF repo')
    else:
        raise ValueError("Must specify name or path to remove challenge")

    shutil.rmtree(path)


def walk_challenges(
    category: str | None = None, *, ignore_errors: bool = False
) -> Generator[Challenge]:
    """
    Walks through all challenges in the challenges folder.
    Can specify a category to only walk through challenges in that category.
    """
    for folder in walk_challenge_folders(category):
        if ignore_errors:
            try:
                yield get_chall_config(folder)
            except ValueError:
                pass
        else:
            yield get_chall_config(folder)


def create_challenge_readme_string(challenge: Challenge) -> str:
    extras = "\n".join(
        f"- **{key.capitalize()}:** {value}" for key, value in challenge.extras.items()
    )

    if challenge.hints is None:
        hints = "None"
    else:
        hints = "\n".join(
            f"- `{hint.content}` ({hint.cost} points)" for hint in challenge.hints
        )

    if challenge.files is None:
        files = "None"
    else:
        files = ""
        for file in challenge.files:
            if isinstance(file, Path):
                files += f"- [{file.name}](<{file.as_posix()}>)\n"
            else:
                files += f"- {file}\n"
        files = files.strip()

    if challenge.flags is None:
        flags = "None"
    else:
        flags = "\n".join(
            f"- `{flag.flag}` ({'regex' if flag.regex else 'static', {'case-sensitive' if flag.case_sensitive else 'case-insensitive'}})"
            for flag in challenge.flags
        )

    if challenge.services is None:
        services = "None"
    else:
        services = "| Service | Port | Type |\n| ------- | ---- | ---- |\n"
        services += "\n".join(
            f"| [`{service.name}`](<{service.path.as_posix()}>) | {service.port} | {service.type} |"
            for service in challenge.services
        )

    readme = CHALL_README_TEMPLATE.format(
        name=challenge.name,
        description=challenge.description,
        author=challenge.author,
        category=challenge.category,
        difficulty=challenge.difficulty,
        extras=extras,
        hints=hints,
        files=files,
        flags=flags,
        services=services,
    )

    return readme
