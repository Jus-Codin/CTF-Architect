"""Functions for repository-level operations."""

from __future__ import annotations

import re
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import overload

from tomlkit import comment, document, dump, load, nl

from ctf_architect.constants import CTF_CONFIG_FILE, CTF_CONFIG_HEADER
from ctf_architect.core.challenge import Challenge
from ctf_architect.core.exceptions import (
    ChallengeExistsError,
    FolderNameCollisionError,
    InvalidCategoryError,
    InvalidChallengeFolderError,
    NotInChallengeRepositoryError,
)
from ctf_architect.core.readmes import render_category_readme, render_repo_readme
from ctf_architect.models.ctf_config import ConfigFile, CTFConfig
from ctf_architect.utils import LRUCache, calculate_difficulty_distribution, is_challenge_folder, is_challenge_repo
from ctf_architect.version import CTF_CONFIG_SPEC_VERSION

# TODO: Not too sure what the ideal max size should be, maybe tweak this in the future
CTF_CONFIG_CACHE: LRUCache[Path, CTFConfig] = LRUCache(max_size=32)


class Repo:
    """A class representing a challenge repository.

    This class provides methods to interact with the challenge repository, such as loading the CTF config,
    walking through challenges, and adding or removing challenges.

    Warning:
        This class should not be instantiated directly. Use the `from_path` method to create an instance.

    Attributes:
        path (Path): The path to the challenge repository.
        ctf_config (CTFConfig): The CTF config object for the repository.
        initialized (bool): Whether the repository has been initialized.
    """

    def __init__(self, path: Path, ctf_config: CTFConfig, initialized: bool = False) -> None:
        self.path = path
        self.ctf_config = ctf_config
        self.initialized = initialized

    @property
    def challenges_path(self) -> Path:
        """Returns the path to the challenges directory."""
        return self.path / "challenges"

    @staticmethod
    def load_config(path: str | Path, ignore_cache: bool = False) -> CTFConfig:
        """Loads the CTF config from the specified path.

        If the path is a file, it will load the CTF config from that file.
        If the path is a directory, it will look for the CTF config file in that

        Args:
            path (str | Path): The path to the CTF config file or directory.
            ignore_cache (bool, optional): Whether to ignore the cache. Defaults to False.

        Returns:
            CTFConfig: The loaded CTF config object.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path.resolve()
        else:
            config_fp = (path / CTF_CONFIG_FILE).resolve()

        if not ignore_cache and config_fp in CTF_CONFIG_CACHE:
            return CTF_CONFIG_CACHE[config_fp]
        else:
            with open(config_fp, encoding="utf-8") as f:
                data = load(f)

            config_file = ConfigFile.model_validate(data.unwrap())

            CTF_CONFIG_CACHE[config_fp] = config_file.config

            return config_file.config

    @staticmethod
    def write_config(path: str | Path, config: CTFConfig) -> None:
        """Writes the CTF config to the specified path.

        If the path is a file, it will be used as the config file.
        If the path is a directory, it will write the config to `ctf_config.toml`

        Args:
            path (str | Path): The folder or file to write the CTF config to.
            config (CTFConfig): The CTF config object to write.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path.resolve()
        else:
            config_fp = (path / CTF_CONFIG_FILE).resolve()

        doc = document()
        for line in CTF_CONFIG_HEADER.splitlines():
            doc.add(comment(line))
        doc.add(nl())

        doc.add("version", str(CTF_CONFIG_SPEC_VERSION))  # type: ignore
        doc.add("config", config.model_dump(mode="json", exclude_defaults=True))  # type: ignore

        with open(config_fp, "w", encoding="utf-8") as f:
            dump(doc, f)

        # If the write was successful, revoke the cache entry
        if config_fp in CTF_CONFIG_CACHE:
            CTF_CONFIG_CACHE.pop(config_fp)

    @classmethod
    def from_path(cls, path: str | Path) -> Repo:
        """Loads a Repo from the specified path.

        Args:
            path (str | Path): The path to the challenge repository.

        Returns:
            Repo: The Repo instance.
        """
        if isinstance(path, str):
            path = Path(path)

        if not is_challenge_repo(path):
            raise NotInChallengeRepositoryError(f'"{path.resolve()}" is not a challenge repository')

        ctf_config = cls.load_config(path)
        return cls(path, ctf_config, initialized=True)

    def save_config(self) -> None:
        """Saves the current CTF config to the repository."""
        self.write_config(self.path, self.ctf_config)

    def refresh(self) -> None:
        """Refreshes the CTF config by reloading it from the repository."""
        self.ctf_config = self.load_config(self.path, ignore_cache=True)

    def get_category_path(self, category: str) -> Path:
        """Returns the path to the specified category in the challenges directory.

        Args:
            category (str): The category to get the path for.

        Returns:
            Path: The path to the specified category.
        """
        return self.challenges_path / category.lower()

    def walk_chall_folders(self, category: str | None = None, *, skip_invalid: bool = True) -> Generator[Path]:
        """Walks through the challenge folders in the repository.

        A category can be optionally specified to filter challenges by category.

        Args:
            category (str, optional): The category to filter challenges by.
            skip_invalid (bool, optional): Whether to skip invalid challenge folders. Defaults to True.

        Yields:
            Generator[Path]: The paths to the valid challenge folders.
        """
        if category is not None:
            # Check if the category exists in the CTF config
            if category.lower() not in self.ctf_config.categories:
                raise InvalidCategoryError(f"Category {category} not in CTF config")
            categories = [category.lower()]
        else:
            categories = self.ctf_config.categories

        for category in categories:
            category_path = self.get_category_path(category)
            if not category_path.exists():
                continue
            for directory in category_path.iterdir():
                if directory.is_dir():
                    if not is_challenge_folder(directory):
                        if skip_invalid:
                            continue
                        raise InvalidChallengeFolderError(f"Invalid challenge folder: {directory}")

                    yield directory

    def find_chall_folder(self, name: str, validate: bool = True) -> Path | None:
        """Finds a challenge folder by name.

        Args:
            name (str): The name of the challenge folder to find.
            validate (bool, optional): Whether to validate the challenge folder. Defaults to True.

        Returns:
            Path | None: The path to the challenge folder if found, None otherwise.
        """
        folders = self.walk_chall_folders(skip_invalid=True)

        # TODO: Convert this to a function for standardization
        folder_name = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", name).strip()

        for folder in folders:
            if folder_name.lower() in folder.name.lower():
                if validate:
                    try:
                        Challenge.load_config(folder)
                        return folder
                    except Exception:
                        pass
                else:
                    return folder

        return None

    def find_challenge(self, name: str) -> Challenge | None:
        """Finds a challenge by name.

        The search is performed in two steps:
        1. Search by the folder name, if a substring match is found, check the
           challenge config file to verify.
        2. Search every challenge config file for an exact name match.

        Args:
            name (str): The name of the challenge to find.

        Returns:
            Challenge | None: The Challenge object if found, None otherwise.
        """
        # Search Strategy:
        # 1. Search by the folder name, if a substring match is found, check the challenge config file to verify.
        # 2. Search every challenge config file for an exact name match

        folders = self.walk_chall_folders(skip_invalid=True)

        searched = set()

        # TODO: Maybe convert this to a function
        folder_name = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", name).strip()

        for folder in folders:
            if folder_name.lower() in folder.name.lower():
                searched.add(folder)
                try:
                    challenge = Challenge.from_path(folder)
                    if challenge.config.name.lower() == name.lower():
                        return challenge
                except Exception:
                    pass

        # Check every challenge config file for a name match
        for folder in folders:
            if folder in searched:
                continue

            try:
                challenge = Challenge.from_path(folder)
                if challenge.config.name.lower() == name.lower():
                    return challenge
            except Exception:
                pass

        return None

    def walk_challenges(
        self,
        category: str | None = None,
        *,
        skip_invalid: bool = False,
        ignore_errors: bool = False,
    ) -> Generator[Challenge, None, None]:
        """Walks through all challenges in the repository.

        A category can be optionally specified to filter challenges by category.

        Args:
            category (str | None, optional): The category to walk through. Defaults to None.
            skip_invalid (bool, optional): Whether to skip invalid challenges. Defaults to False.
            ignore_errors (bool, optional): Whether to ignore errors. Defaults to False.

        Yields:
            Generator[Challenge]: The Challenge objects.
        """
        for folder in self.walk_chall_folders(category, skip_invalid=skip_invalid):
            if ignore_errors:
                try:
                    yield Challenge.from_path(folder)
                except Exception:
                    pass
            else:
                yield Challenge.from_path(folder)

    @overload
    def add_challenge(
        self,
        challenge_or_folder: Challenge,
        /,
        replace_existing: bool = False,
        preserve_original: bool = False,
    ) -> None: ...

    @overload
    def add_challenge(
        self,
        challenge_or_folder: str | Path,
        /,
        replace_existing: bool = False,
        preserve_original: bool = False,
    ) -> None: ...

    def add_challenge(
        self,
        challenge_or_folder: str | Path | Challenge,
        /,
        replace_existing: bool = False,
        preserve_original: bool = False,
    ) -> None:
        """Adds a challenge to the repository.

        The challenge can be specified as either a `Challenge` object or a path to the challenge folder.
        If `replace_existing` is True, it will overwrite the existing challenge if it has the same name.
        If `preserve_original` is True, it will preserve the original challenge folder and copy it to the new location.

        Note:
            Both the challenge and repository must be initialized before adding a challenge.

        Args:
            challenge_or_folder (str | Path | Challenge): The challenge to add, either as a `Challenge` object or a path to the challenge folder.
            replace_existing (bool, optional): Whether to overwrite an existing challenge with the same name. Defaults to False.
            preserve_original (bool, optional): Whether to preserve the original challenge folder. Defaults to False.

        Raises:
            NotADirectoryError: The specified path is not a directory.
            InvalidCategoryError: The category of the challenge is not in the CTF config.
            ChallengeExistsError: A challenge with the same name already exists.
            FolderNameCollisionError: Another challenge is using the same folder name.
        """
        if not self.initialized:
            raise RuntimeError(
                "Cannot add a challenge to an uninitialized repository. Please initialize the repository first."
            )

        if isinstance(challenge_or_folder, Challenge):
            challenge = challenge_or_folder
        else:
            chall_folder = Path(challenge_or_folder)
            challenge = Challenge.from_path(chall_folder)

        # Check if the category exists
        # This is to prevent a challenge from being added to a category that doesn't exist
        if challenge.config.category not in self.ctf_config.categories:
            raise InvalidCategoryError(f"Category {challenge.config.category} not in CTF config")

        # Check if path for the challenge already exists
        if (self.path / challenge.repo_path).exists():
            # Check if the challenge in that path is the same name as the new challenge
            old_challenge = Challenge.from_path(self.path / challenge.repo_path)
            if old_challenge.config.name == challenge.config.name:
                if replace_existing:
                    self.remove_challenge(folder=old_challenge.repo_path)
                else:
                    raise ChallengeExistsError(f"Challenge with name {challenge.config.name} already exists")
            else:
                # Folder name collision
                raise FolderNameCollisionError(
                    "Another challenge is using the same folder name. Please resolve the conflict.\n"
                    f"  Old Challenge: {old_challenge.config.name}\n"
                    f"  New Challenge: {challenge.config.name}"
                )

        # Check if a challenge with the same name already exists
        # Technically, if a challenge in another category has the same name, they can coexist
        # However, this will most likely lead to confusion and potential issues down the line during deployment
        elif (c := self.find_challenge(challenge.config.name)) is not None:
            if replace_existing:
                self.remove_challenge(folder=c.repo_path)
            else:
                raise ChallengeExistsError(f"Challenge with name {c.config.name} already exists")

        new_path = self.path / challenge.repo_path
        if preserve_original:
            challenge.copy_to(new_path, as_subfolder=False)
        else:
            challenge.move_to(new_path, as_subfolder=False)

    @overload
    def remove_challenge(self, *, name: str) -> None: ...

    @overload
    def remove_challenge(self, *, folder: str | Path) -> None: ...

    @overload
    def remove_challenge(self, *, challenge: Challenge) -> None: ...

    def remove_challenge(
        self,
        *,
        name: str | None = None,
        folder: str | Path | None = None,
        challenge: Challenge | None = None,
    ) -> None:
        """Removes a challenge from the repository.

        Can specify either the name, folder path, or a Challenge object to remove.

        Args:
            name (str | None, optional): The name of the challenge to remove. Defaults to None. Keyword-only.
            folder (str | Path | None, optional): The path to the challenge folder to remove. Defaults to None. Keyword-only.
            challenge (Challenge | None, optional): The Challenge object to remove. Defaults to None. Keyword-only.

        Raises:
            RuntimeError: The repository is not initialized.
            ValueError: More than one, or none of name, folder, or challenge is specified.
            FileNotFoundError: The challenge with the specified name is not found.
            NotADirectoryError: The specified path is not a directory.
            NotInChallengeRepositoryError: The specified path is not in the challenge repository.
        """
        if not self.initialized:
            raise RuntimeError(
                "Cannot remove a challenge from an uninitialized repository. Please initialize the repository first."
            )

        if (name, folder, challenge).count(None) != 2:
            raise ValueError("Must specify only one of name, folder, or challenge to remove")

        if name is not None:
            challenge = self.find_challenge(name)
            if challenge is None:
                raise FileNotFoundError(f"Challenge with name {name} not found")
            folder = challenge.repo_path
        elif folder is not None:
            if isinstance(folder, str):
                folder = Path(folder)
            if not folder.is_dir():
                raise NotADirectoryError(f'"{folder.absolute()}" is not a directory')
            # Safety check to make sure path is in the challenge repo
            if folder.resolve().parent != (self.path / "challenges").resolve():
                raise NotInChallengeRepositoryError(f'"{folder.absolute()}" is not in the CTF repo')
        elif challenge is not None:
            folder = challenge.repo_path
        else:
            raise ValueError("Must specify one of name, folder, or challenge to remove")

        shutil.rmtree(folder)

    def get_category_readme(self, category: str) -> str:
        """Generates the README for a specific category.

        Args:
            category (str): The category to generate the README for.

        Returns:
            str: The generated README content for the specified category.
        """
        if not self.initialized:
            raise RuntimeError(
                "Cannot generate category README from an uninitialized repository. Please initialize the repository first."
            )

        if category.lower() not in self.ctf_config.categories:
            raise InvalidCategoryError(f"Category {category} not in CTF config")

        challenges = []
        services = []
        for challenge in self.walk_challenges(category=category, skip_invalid=True):
            challenges.append(challenge.config)
            if challenge.config.services is not None:
                for service in challenge.config.services:
                    services.append((service, challenge.config))

        distribution = calculate_difficulty_distribution(challenges)

        return render_category_readme(
            category_name=category,
            ctf_config=self.ctf_config,
            distribution=distribution,
            challenges=challenges,
            services=services,
        )

    def get_repo_readme(self) -> str:
        """Generates the repository README.

        Returns:
            str: The generated README content for the repository.
        """
        if not self.initialized:
            raise RuntimeError(
                "Cannot generate repository README from an uninitialized repository. Please initialize the repository first."
            )

        distributions = {}
        challenges = []
        services = []
        for category in self.ctf_config.categories:
            distributions[category] = {}
            for challenge in self.walk_challenges(category=category, skip_invalid=True):
                diff = challenge.config.difficulty
                distributions[category][diff] = distributions[category].get(diff, 0) + 1
                challenges.append(challenge.config)
                if challenge.config.services is not None:
                    for service in challenge.config.services:
                        services.append((service, challenge.config))

        # Compute total distribution
        distributions["_total"] = {
            diff: sum(d.get(diff, 0) for d in distributions.values()) for diff in self.ctf_config.difficulties
        }

        return render_repo_readme(
            ctf_config=self.ctf_config,
            distributions=distributions,
            challenges=challenges,
            services=services,
        )

    def save_category_readme(self, category: str) -> None:
        """Saves the README for a specific category to the category folder.

        Args:
            category (str): The category to save the README for.
        """
        if not self.initialized:
            raise RuntimeError(
                "Cannot save category README from an uninitialized repository. Please initialize the repository first."
            )

        if category.lower() not in self.ctf_config.categories:
            raise InvalidCategoryError(f"Category {category} not in CTF config")

        readme_content = self.get_category_readme(category)
        category_path = self.get_category_path(category)
        readme_fp = category_path / "README.md"
        readme_fp.write_text(readme_content, encoding="utf-8")

    def save_repo_readme(self) -> None:
        """Saves the repository README to the root of the repository."""
        if not self.initialized:
            raise RuntimeError(
                "Cannot save repository README from an uninitialized repository. Please initialize the repository first."
            )

        readme_content = self.get_repo_readme()
        readme_fp = self.challenges_path / "README.md"
        readme_fp.write_text(readme_content, encoding="utf-8")

    def save_all_readmes(self) -> None:
        """Saves all README files for the repository."""
        if not self.initialized:
            raise RuntimeError(
                "Cannot save all README files from an uninitialized repository. Please initialize the repository first."
            )

        for category in self.ctf_config.categories:
            self.save_category_readme(category)

        self.save_repo_readme()

    @classmethod
    def new(cls, path: str | Path, ctf_config: CTFConfig, config_file_only: bool = False) -> Repo:
        """Creates a new challenge repository at the specified path.

        Args:
            path (str | Path): The path to create the new repository at.
            ctf_config (CTFConfig): The CTF config object for the new repository.
            config_file_only (bool, optional): If True, only creates the CTF config file without the challenges directory. Defaults to False.

        Returns:
            Repo: The newly created Repo instance.
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.is_dir():
            raise NotADirectoryError(f'"{path.absolute()}" is not a directory')

        cls.write_config(path, ctf_config)

        if config_file_only:
            return cls(path, ctf_config, initialized=False)

        repo = cls(path, ctf_config, initialized=True)

        challenges_path = path / "challenges"
        challenges_path.mkdir(parents=True, exist_ok=True)

        # Create the folders for each category and initialize the readme
        for category in ctf_config.categories:
            (challenges_path / category).mkdir(parents=True, exist_ok=True)
            repo.save_category_readme(category)

        # Initialize the root readme
        repo.save_repo_readme()

        return repo
