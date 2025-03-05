"""Functions for repository-level operations."""

import re
import shutil
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from tomlkit import comment, document, dump, load, nl

from ctf_architect.constants import CTF_CONFIG_FILE, CTF_CONFIG_HEADER
from ctf_architect.core.challenge import is_challenge_folder, load_chall_config
from ctf_architect.core.exceptions import (
    ChallengeExistsError,
    FolderNameCollisionError,
    InvalidCategoryError,
    InvalidChallengeFolderError,
    NotInChallengeRepositoryError,
)
from ctf_architect.models.challenge import Challenge
from ctf_architect.models.ctf_config import ConfigFile, CTFConfig
from ctf_architect.version import CTF_CONFIG_SPEC_VERSION


def is_challenge_repo(path: str | Path | None = None) -> bool:
    """Checks if the current given path is a challenge repo.

    If no path is specified, the current working directory is checked.

    A challenge repo is considered valid if it has a CTF config file and a challenges directory.

    Args:
        path (str | Path, optional): The path to check. Defaults to None.

    Returns:
        bool: True if the given path is a challenge repo, False otherwise.
    """
    if path is None:
        path = Path.cwd()
    elif isinstance(path, str):
        path = Path(path)

    if path.is_dir():
        if (path / "challenges").is_dir() and (path / CTF_CONFIG_FILE).is_file():
            return True
        else:
            return False

    return False


@lru_cache
def load_repo_config(path: str | Path | None = None) -> CTFConfig:
    """Loads the CTF config file from the given path.

    If no path is specified, the CTF config file is loaded from the current working directory.
    If the path is a file, it is loaded directly, else the CTF config file is loaded from the specified directory.

    Args:
        path (str | Path | None, optional): The path to the CTF config file or directory. Defaults to None.

    Returns:
        CTFConfig: The CTF config object.

    Raises:
        FileNotFoundError: If the CTF config file is not found in the specified directory.
    """
    if path is None:
        path = Path.cwd()
    elif isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Could not find {CTF_CONFIG_FILE} in {path}")

    if path.is_dir():
        # If path is a valid repo, load the CTF config file from the directory
        if is_challenge_repo(path):
            ctf_config_file = path / CTF_CONFIG_FILE
        else:
            raise NotInChallengeRepositoryError(f'"{path.resolve()}" is not a challenge repository')
    else:
        ctf_config_file = path

    with open(ctf_config_file, encoding="utf-8") as f:
        data = load(f)

    config_file = ConfigFile.model_validate(data.unwrap())

    return config_file.config


def save_repo_config(config: CTFConfig) -> None:
    """Saves the CTF config object to the CTF config file in the current working directory."""
    doc = document()
    for line in CTF_CONFIG_HEADER.splitlines():
        doc.add(comment(line))
    doc.add(nl())

    doc.add("version", str(CTF_CONFIG_SPEC_VERSION))  # type: ignore
    doc.add("config", config.model_dump(mode="json", exclude_defaults=True))  # type: ignore

    with open(CTF_CONFIG_FILE, "w", encoding="utf-8") as f:
        dump(doc, f)


def walk_challenge_folders(category: str | None = None, *, ignore_invalid: bool = True) -> Generator[Path]:
    """Walks through all challenge folders in the challenges directory.

    Can specify a category to only walk through challenges in that category.

    Args:
        category (str | None, optional): The category to walk through. Defaults to None.
        ignore_invalid (bool, optional): Whether to ignore invalid challenge folders. Defaults to True. Keyword-only.

    Yields:
        Path: The path to the challenge folder.

    Raises:
        InvalidCategoryError: If the category is not in the CTF config.
        InvalidChallengeFolderError: If the challenge folder is invalid.
    """
    config = load_repo_config()

    challenges_path = Path("challenges")

    if category is not None:
        if category.lower() not in config.categories:
            raise InvalidCategoryError(f"Category {category} not in CTF config")
        categories = [category.lower()]
    else:
        categories = config.categories

    for category in categories:
        if not (challenges_path / category).exists():
            continue
        for directory in (challenges_path / category).iterdir():
            if directory.is_dir():
                if not is_challenge_folder(directory):
                    if ignore_invalid:
                        continue
                    raise InvalidChallengeFolderError(f"Invalid challenge folder: {directory}")

                yield directory


def find_challenge_folder(name: str, verify: bool = True) -> Path | None:
    """Finds a challenge folder with the given name.

    Args:
        name (str): The name of the challenge folder to find.
        verify (bool, optional): Whether to verify the challenge folder. Defaults to True.

    Returns:
        Path | None: The path to the challenge folder if found, None otherwise.
    """
    folders = walk_challenge_folders(ignore_invalid=True)

    folder_name = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", name).strip()

    for folder in folders:
        if folder_name.lower() in folder.name.lower():
            if verify:
                try:
                    load_chall_config(folder)
                    return folder
                except Exception:
                    pass
            else:
                return folder


def find_challenge(name: str) -> Challenge | None:
    """Finds a challenge with the given name.

    Args:
        name (str): The name of the challenge to find.

    Returns:
        Challenge | None: The challenge object if found, None otherwise.
    """
    # Search Strategy:
    # 1. Search by the folder name, if match found, check challenge config file to verify
    # 2. Search every challenge config file for a name match

    folders = walk_challenge_folders(ignore_invalid=True)

    searched = set()

    # TODO: Maybe convert this to a function
    folder_name = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", name).strip()

    for folder in folders:
        if folder_name.lower() in folder.name.lower():
            searched.add(folder)
            try:
                challenge = load_chall_config(folder)
                if challenge.name.lower() == name.lower():
                    return challenge
            except Exception:
                pass

    for folder in folders:
        if folder in searched:
            continue

        try:
            challenge = load_chall_config(folder)
            if challenge.name.lower() == name.lower():
                return challenge
        except Exception:
            pass

    return None


def add_challenge(folder: str | Path, replace: bool = False) -> None:
    """Adds a challenge from the specified path to the challenges directory.

    If replace is True, will overwrite the challenge if it already exists.

    Args:
        folder (str | Path): The path to the challenge folder to add.
        replace (bool, optional): Whether to overwrite the challenge if it already exists. Defaults to False.

    Raises:
        NotADirectoryError: If the specified path is not a directory.
        InvalidCategoryError: If the category is not in the CTF config.
        ChallengeExistsError: If a challenge with the same name already exists.
        FolderNameCollisionError: If another challenge is using the same folder name.
    """
    if isinstance(folder, str):
        folder = Path(folder)

    if not folder.is_dir():
        raise NotADirectoryError(f'"{folder.absolute()}" is not a directory')

    config = load_repo_config()

    challenge = load_chall_config(folder)

    # Check if the category exists
    # This is to prevent a challenge from being added to a category that doesn't exist
    if challenge.category not in config.categories:
        raise InvalidCategoryError(f"Category {challenge.category} not in CTF config")

    # Check if path for the challenge already exists
    if challenge.repo_path.exists():
        # Check if the challenge in that path is the same name as the new challenge
        old_challenge = load_chall_config(challenge.repo_path)
        if old_challenge.name == challenge.name:
            if replace:
                remove_challenge(folder=challenge.repo_path)
            else:
                raise ChallengeExistsError(f"Challenge with name {challenge.name} already exists")
        else:
            # Folder name collision
            raise FolderNameCollisionError(
                "Another challenge is using the same folder name. Please resolve the conflict.\n"
                f"  Old Challenge: {old_challenge.name}\n"
                f"  New Challenge: {challenge.name}"
            )

    # Check if a challenge with the same name already exists
    # Honestly if the challenge is in another category, we can have the same name
    # but it's probably better practice to not have the same name
    elif (c := find_challenge(challenge.name)) is not None:
        if replace:
            remove_challenge(folder=c.repo_path)
        else:
            raise ChallengeExistsError(f"Challenge with name {c.name} already exists")

    new_path = challenge.repo_path
    folder.rename(new_path)


def remove_challenge(*, name: str | None = None, folder: str | Path | None = None) -> None:
    """Removes a challenge from the challenges directory.

    Can specify either the name or the path to the challenge folder.

    Args:
        name (str | None, optional): The name of the challenge to remove. Defaults to None. Keyword-only.
        folder (str | Path | None, optional): The path to the challenge folder to remove. Defaults to None. Keyword-only.

    Raises:
        ValueError: If both name and folder are specified.
        FileNotFoundError: If the challenge with the specified name is not found.
        NotADirectoryError: If the specified path is not a directory.
        NotInChallengeRepositoryError: If the specified path is not in the challenge repository.

    Returns:
        None
    """
    if name is not None and folder is not None:
        raise ValueError("Can only specify name or folder, not both")

    if name is not None:
        challenge = find_challenge(name)
        if challenge is None:
            raise FileNotFoundError(f"Challenge with name {name} not found")
        folder = challenge.repo_path
    elif folder is not None:
        if isinstance(folder, str):
            folder = Path(folder)
        if not folder.is_dir():
            raise NotADirectoryError(f'"{folder.absolute()}" is not a directory')
        # Safety check to make sure path is in the challenge repo
        if folder.resolve().parent not in Path("challenges").resolve().iterdir():
            raise NotInChallengeRepositoryError(f'"{folder.absolute()}" is not in the CTF repo')
    else:
        raise ValueError("Must specify name or path to remove challenge")

    shutil.rmtree(folder)


def walk_challenges(
    category: str | None = None,
    *,
    ignore_invalid: bool = False,
    ignore_errors: bool = False,
) -> Generator[Challenge, None, None]:
    """Walks through all challenges in the challenges folder.

    Can specify a category to only walk through challenges in that category.

    Args:
        category (str | None, optional): The category to walk through. Defaults to None.
        ignore_invalid (bool, optional): Whether to ignore invalid challenges. Defaults to False.
        ignore_errors (bool, optional): Whether to ignore errors. Defaults to False.

    Yields:
        Challenge: The challenge object.
    """
    for folder in walk_challenge_folders(category, ignore_invalid=ignore_invalid):
        if ignore_errors:
            try:
                yield load_chall_config(folder)
            except Exception:
                pass
        else:
            yield load_chall_config(folder)
