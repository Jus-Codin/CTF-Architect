from __future__ import annotations

import os
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
from ctf_architect.core.models import Challenge, ChallengeFile, CTFConfig


def is_challenge_folder(path: str | Path) -> bool:
    files = os.listdir(path)

    # Do case insensitive check for challenge config and readme
    has_chall_config = False
    has_readme_md = False

    for file in files:
        if file.lower() == CHALLENGE_CONFIG_FILE:
            has_chall_config = True
        if file.lower() == "readme.md":
            has_readme_md = True

    return has_chall_config and has_readme_md


def is_challenge_repo() -> bool:
    """
    Checks if the current working directory is a challenge repo.

    A challenge repo is considered valid if it has a CTF config file and a challenges directory
    """
    return Path(CTF_CONFIG_FILE).exists() and Path("challenges").exists()


def verify_challenge_config(
    challenge: Challenge, config: CTFConfig | None = None
) -> None:
    if config is None:
        config = load_config()

    if challenge.category not in config.categories:
        raise ValueError(f"Category {challenge.category} not in CTF config")

    if challenge.difficulty not in [d.name for d in config.difficulties]:
        raise ValueError(f"Difficulty {challenge.difficulty} not in CTF config")

    for extra in config.extras:
        if extra not in challenge.extras:
            raise ValueError(f'Required extra value "{extra}" not in challenge config')


def get_chall_config(path: str | Path, verify: bool = False) -> Challenge:
    if isinstance(path, str):
        path = Path(path)

    if not is_challenge_folder(path):
        raise FileNotFoundError("Challenge does not have chall.yaml or README.md")

    with (path / CHALLENGE_CONFIG_FILE).open("r", encoding="utf-8") as f:
        data = load(f)

    try:
        config_file = ChallengeFile.model_validate(data.unwrap())
    except ValidationError as e:
        raise ValueError(f"Error loading challenge config file: {e}")

    challenge = config_file.challenge

    if verify:
        try:
            verify_challenge_config(challenge)
        except ValueError as e:
            raise ValueError(f"Error verifying challenge config:\n{e}")

    return challenge


def find_challenge(name: str) -> tuple[Challenge, Path] | None:
    """
    Tries to find a challenge with the given name.
    Returns a tuple of the challenge info and the path to the challenge folder.
    """

    # Search Strategy:
    # 1. Search by the folder name, if match found, check challenge config file to verify
    # 2. Search every challenge config file for a name match

    config = load_config()

    challenges_path = Path("challenges")

    # Get all possible challenge folders
    folders: list[Path] = []
    for category in config.categories:
        for directory in (challenges_path / category).iterdir():
            if directory.is_dir():
                folders.append(directory)

    searched = []

    folder_name = re.sub(r"[^a-zA-Z0-9-_ ]", "", name).strip()

    for folder in folders:
        if folder_name.lower() in folder.name.lower():
            searched.append(folder)
            try:
                challenge = get_chall_config(folder, verify=True)
                if challenge.name.lower() == name.lower():
                    return challenge, folder
            except ValueError:
                pass

    for folder in folders:
        if folder in searched:
            continue
        try:
            challenge = get_chall_config(folder, verify=True)
            if challenge.name.lower() == name.lower():
                return challenge, folder
        except ValueError:
            pass


def add_challenge(
    folder: str | Path, replace: bool = False, verify: bool = True
) -> None:
    """
    Adds a challenge from the specified path to the challenges folder.

    If replace is True, will overwrite the challenge if it already exists.
    If verify is True, will verify the challenge before adding it.
    """
    if isinstance(folder, str):
        folder = Path(folder)

    if not folder.is_dir():
        raise ValueError(f'"{folder.absolute()}" is not a directory')

    challenge = get_chall_config(folder, verify=verify)

    # Check if path for the challenge already exists
    if challenge.full_path.exists():
        # Check if the challenge in that path is the same name as the new challenge
        old_challenge = get_chall_config(challenge.full_path)
        if old_challenge.name == challenge.name:
            if replace:
                remove_challenge(path=challenge.full_path)
            else:
                raise FileExistsError(
                    f"Challenge with name {challenge.name} already exists"
                )
        else:
            # If the challenge in that path is a different name, raise an error
            raise FileExistsError(
                f"A challenge with a similar name already exists in the same category, unable to resolve conflict.\n    Old Challenge: {old_challenge.name}\n   New Challenge: {challenge.name}"
            )

    elif (c := find_challenge(challenge.name)) is not None:
        if replace:
            remove_challenge(path=c[1])
        else:
            raise FileExistsError(
                f"Challenge with name {challenge.name} already exists"
            )

    # Move the challenge to the correct category folder
    new_path = challenge.full_path
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
        path = challenge[1]
    elif path is not None:
        if isinstance(path, str):
            path = Path(path)
        if not path.is_dir():
            raise ValueError(f'"{path.absolute()}" is not a directory')
    else:
        raise ValueError("Must specify name or path to remove challenge")

    shutil.rmtree(path)


def walk_challenges(
    category: str | None = None, *, verify: bool = False
) -> Generator[Challenge]:
    """
    Walks through all challenges in the challenges folder.
    Can specify a category to only walk through challenges in that category.
    """
    config = load_config()

    challenges_path = Path("challenges")

    if category is not None:
        if category not in config.categories:
            raise ValueError(f"Category {category} not in CTF config")
        categories = [category]
    else:
        categories = config.categories

    for category in categories:
        for directory in (challenges_path / category).iterdir():
            if directory.is_dir():
                try:
                    yield get_chall_config(directory, verify=verify)
                except ValueError:
                    pass


def create_challenge_readme(challenge: Challenge):
    flags = "\n".join(
        f"- `{flag.flag}` ({'regex' if flag.regex else 'static'})"
        for flag in challenge.flags
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
                files += f"- [{file.name}]({file})\n"
            else:
                files += f"- {file}\n"
        files = files.strip()

    if challenge.services is None:
        services = "None"
    else:
        services = "| Service | Port | Type |\n| ------- | ---- | ---- |\n"
        services += "\n".join(
            f"| [`{service.name}`]({service.path}) | {service.port} | {service.type} |"
            for service in challenge.services
        )

    extras = "\n".join(
        f"- **{key.capitalize()}:** {value}" for key, value in challenge.extras.items()
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
