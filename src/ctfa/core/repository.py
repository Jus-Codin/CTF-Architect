from __future__ import annotations

import re
import shutil
from collections.abc import Iterator
from pathlib import Path

from ctfa.constants import CTF_CONFIG_FILE, CTF_CONFIG_HEADER, CTF_CONFIG_SPEC_VERSION
from ctfa.core.challenge import Challenge
from ctfa.core.exceptions import (
    CategoryNotFoundError,
    ChallengeExistsError,
    ChallengeNotFoundError,
    ConfigFileNotFoundError,
    FolderNameCollisionError,
    FolderOutsideRepositoryError,
    InvalidChallengeRepositoryError,
    InvalidParameterError,
    PathExistsAsFileError,
    PathIsNotDirectoryError,
)
from ctfa.core.render import render_category_readme as _render_category_readme
from ctfa.core.render import render_repo_readme as _render_repo_readme
from ctfa.models.ctf_config import CTFConfig, RepositoryConfigFile
from ctfa.utils import (
    calculate_difficulty_distribution,
    get_ctf_config_file,
    is_challenge_folder,
    is_challenge_repo,
    yaml,
)
from ruamel.yaml.comments import CommentedMap


class ChallengeRepository:
    """Represents a Challenge Repository.

    Attributes:
        location (Path): The path to the repository.
        ctf_config (CTFConfig): The CTF configuration for the repository.
    """

    def __init__(self, repo_path: Path, ctf_config: CTFConfig):
        self.location = repo_path.resolve()
        self.ctf_config = ctf_config

    @property
    def challenges_path(self) -> Path:
        """The path to the challenges directory in the repository."""
        return self.location / "challenges"

    @staticmethod
    def load_config_file(path: str | Path) -> CTFConfig:
        """Loads a CTF Config file from the specified path.

        If the path specified is a file, it will load the config from the file directly.
        Else, it will look for the `ctf_config.yaml` file in the specified directory.

        Args:
            path (str | Path): The path to the CTF Config file or directory

        Raises:
            FileNotFoundError: If no CTF config file is found at the specified path

        Returns:
            CTFConfig: The loaded CTFConfig object
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = get_ctf_config_file(path)
            if config_fp is None:
                raise ConfigFileNotFoundError(path, "CTF config")

        with config_fp.open("r", encoding="utf-8") as f:
            data = yaml.load(f)

        config_file = RepositoryConfigFile.model_validate(data)

        return config_file.config

    @staticmethod
    def dump_config_file(path: str | Path, ctf_config: CTFConfig) -> None:
        """Dumps a CTF Config File to an existing fole or to a challenge repository.

        If the path specified is an existing file, it will dump the config into the file directly.
        Else, it will dump the config file in the specified directory.

        Args:
            ctf_config (CTFConfig): The CTFConfig object to dump
            path (str | Path): The path to the CTF Config file or directory
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = path / CTF_CONFIG_FILE

        ctf_config_data = CommentedMap(
            ctf_config.model_dump(mode="json", exclude_defaults=True)
        )

        # Add spacing between top-level dict or list keys
        for key, value in ctf_config_data.items():
            if isinstance(value, list | dict):
                ctf_config_data.yaml_set_comment_before_after_key(key, before="\n")

        file_data = CommentedMap(
            {
                "version": str(CTF_CONFIG_SPEC_VERSION),
                "config": ctf_config_data,
            }
        )

        # Add header comment
        file_data.yaml_set_start_comment(CTF_CONFIG_HEADER + "\n")

        # Add spacing before "config" key
        file_data.yaml_set_comment_before_after_key("config", before="\n")

        with config_fp.open("w", encoding="utf-8") as f:
            yaml.dump(file_data, f)

    @classmethod
    def load_repository(cls, repo_path: str | Path) -> ChallengeRepository:
        """Loads a Challenge Repository from the specified path.

        Args:
            repo_path (str | Path): The path to the repository

        Returns:
            ChallengeRepository: The challenge repository instance.
        """
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)

        if not is_challenge_repo(repo_path):
            raise InvalidChallengeRepositoryError(repo_path)

        ctf_config = cls.load_config_file(repo_path)

        return cls(repo_path, ctf_config)

    @classmethod
    def create_config_only(cls, repo_path: str | Path, ctf_config: CTFConfig) -> None:
        """Creates only the CTF Config file for a Challenge Repository.

        Args:
            repo_path (str | Path): The path to create the repository at.
            ctf_config (CTFConfig): The CTF configuration for the repository.
        """
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)

        if repo_path.exists() and not repo_path.is_dir():
            raise PathExistsAsFileError(repo_path)

        repo_path.mkdir(parents=True, exist_ok=True)

        cls.dump_config_file(repo_path, ctf_config)

    @classmethod
    def create(
        cls, repo_path: str | Path, ctf_config: CTFConfig
    ) -> ChallengeRepository:
        """Creates a new Challenge Repository at the specified path.

        Args:
            repo_path (str | Path): The path to create the repository at.
            ctf_config (CTFConfig): The CTF configuration for the repository.

        Returns:
            ChallengeRepository: The created challenge repository instance.
        """
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)

        if repo_path.exists() and not repo_path.is_dir():
            raise PathExistsAsFileError(repo_path)

        repo_path.mkdir(parents=True, exist_ok=True)

        cls.dump_config_file(repo_path, ctf_config)

        challenges_path = repo_path / "challenges"
        challenges_path.mkdir(exist_ok=True)

        repo = cls.load_repository(repo_path)

        # Create category directories and initial README files
        for category in ctf_config.categories:
            category_path = challenges_path / category.lower()
            category_path.mkdir(exist_ok=True)
            repo.save_category_readme(category)

        repo.save_repository_readme()

        return repo

    def reload(self) -> None:
        """Reloads the CTF Config for the repository."""
        self.ctf_config = self.load_config_file(self.location)

    def save_config(self) -> None:
        """Saves the current CTF Config to the repository."""
        self.dump_config_file(self.location, self.ctf_config)

    def get_category_path(self, category: str) -> Path:
        """Gets the path to the specified category in the repository.

        Args:
            category (str): The category name.

        Returns:
            Path: The path to the specified category.
        """
        return self.challenges_path / category.lower()

    # ----------------------------------------------------------------
    # Challenge Folder Accessing
    # ----------------------------------------------------------------

    def walk_challenge_folders(
        self, category: str | None = None, *, skip_invalid: bool = True
    ) -> Iterator[Path]:
        """Walks through all challenge folders in the repository.

        Args:
            category (str, optional): The category to filter challenges by. If None, all categories are included.
            skip_invalid (bool): Whether to skip invalid challenge folders. Defaults to True.

        Yields:
            Iterator[Path]: An iterator of Paths to challenge folders.
        """
        if category is not None:
            # Check if the category exists in the CTF config
            if category.lower() not in self.ctf_config.categories:
                raise CategoryNotFoundError(category)
            categories = [category.lower()]
        else:
            categories = self.ctf_config.categories

        for category in categories:
            category_path = self.get_category_path(category)
            if not category_path.exists():
                continue

            for item in category_path.iterdir():
                if not item.is_dir():
                    continue

                if not is_challenge_folder(item):
                    if skip_invalid:
                        continue
                    from ctfa.core.exceptions import InvalidChallengeFolderError

                    raise InvalidChallengeFolderError(item)

                yield item

    def find_challenge_folder(self, name: str, validate: bool = True) -> Path | None:
        """Finds a challenge folder by folder name in the repository.

        Note: If the challenge has an ID not based on the challenge name, you might need to search twice.

        Args:
            name (str): The name of the challenge folder to find.
            validate (bool): Whether to validate the challenge folder. Defaults to True.

        Returns:
            Path | None: The path to the challenge folder if found, else None.
        """
        # Sanitize the name for comparison
        folder_name = (
            re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9 _-]", "", name).strip().lower()
        )

        for folder in self.walk_challenge_folders(skip_invalid=True):
            if folder_name == folder.name.lower():
                if validate:
                    try:
                        Challenge.load_folder(folder)
                        return folder
                    except Exception:
                        continue
                else:
                    return folder

        return None

    def find_challenge(self, query: str) -> Challenge | None:
        """Finds a challenge by name, ID, or folder name in the repository.

        The search is performed in the following order:
        1. Search by folder name, if a match is found, load and check the challenge ID or name.
        2. Search every challenge folder and check the challenge ID or name.

        Args:
            query (str): The name, ID, or folder name of the challenge to find.

        Returns:
            Challenge | None: The Challenge object if found, else None.
        """
        unloaded_challenges = set()

        maybe_folder_name = (
            re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9 _-]", "", query).strip().lower()
        )

        # First pass, find by folder name
        for folder in self.walk_challenge_folders(skip_invalid=True):
            if maybe_folder_name == folder.name.lower():
                try:
                    challenge = Challenge.load_folder(folder)
                    # Check for exact ID or case-insensitive name match
                    if (
                        challenge.config.id == query
                        or challenge.config.name.lower() == query.lower()
                    ):
                        return challenge
                except Exception:
                    pass
            else:
                unloaded_challenges.add(folder)

        # Second pass, check every unloaded challenge folder
        for folder in unloaded_challenges:
            try:
                challenge = Challenge.load_folder(folder)
                # Check for exact ID or case-insensitive name match
                if (
                    challenge.config.id == query
                    or challenge.config.name.lower() == query.lower()
                ):
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
    ) -> Iterator[Challenge]:
        """Walks through all challenges in the repository.

        Args:
            category (str, optional): The category to filter challenges by. If None, all categories are included.
            skip_invalid (bool): Whether to skip invalid challenge folders. Defaults to False.
            ignore_errors (bool): Whether to ignore errors when loading challenges. Defaults to False.

        Yields:
            Iterator[Challenge]: An iterator of Challenge objects.
        """
        for folder in self.walk_challenge_folders(category, skip_invalid=skip_invalid):
            if ignore_errors:
                try:
                    yield Challenge.load_folder(folder)
                except Exception:
                    continue
            else:
                yield Challenge.load_folder(folder)

    # ----------------------------------------------------------------
    # Challenge Folder Management
    # ----------------------------------------------------------------

    def add_challenge(
        self,
        challenge_or_folder: str | Path | Challenge,
        replace_existing: bool = False,
        preserve_original: bool = False,
    ) -> None:
        """Adds a challenge folder to the repository.

        The challenge can be specified as either a `Challenge` object or a path to an existing challenge folder.
        If `replace_existing` is True, any existing challenge with the same ID will be replaced.
        If `preserve_original` is True, the original challenge folder will be copied instead of moved.

        Args:
            challenge_or_folder (str | Path | Challenge): The challenge or path to the challenge folder to add.
            replace_existing (bool): Whether to replace an existing challenge with the same ID. Defaults to False.
            preserve_original (bool): Whether to preserve the original challenge folder when adding. Defaults to False.

        Raises:
            CategoryNotFoundError: If the challenge's category does not exist in the CTF config.
            ChallengeExistsError: If a challenge with the same ID already exists and `replace_existing` is False.
            FolderNameCollisionError: If the target folder exists with a different challenge ID.
        """
        if isinstance(challenge_or_folder, Challenge):
            challenge = challenge_or_folder
        else:
            challenge = Challenge.load_folder(Path(challenge_or_folder))

        # Check if the category exists
        if challenge.config.category not in self.ctf_config.categories:
            raise CategoryNotFoundError(challenge.config.category)

        # Check if challenge folder already exists
        if (self.location / challenge.repository_path).exists():
            # Check if the challenge in that path is the same name as the new challenge
            existing_challenge = Challenge.load_folder(
                self.location / challenge.repository_path
            )
            if existing_challenge.config.id == challenge.config.id:
                if replace_existing:
                    self.remove_challenge(folder=existing_challenge.repository_path)
                else:
                    raise ChallengeExistsError(
                        challenge.config.id, existing_challenge.repository_path
                    )
            else:
                raise FolderNameCollisionError(
                    existing_challenge.config.id,
                    challenge.config.id,
                    existing_challenge.repository_path,
                )

        # Check if a challenge with the same ID already exists
        # Technically, this works if it conflicts with a challenge in a different category
        # but it could cause some confusion, so we check for it anyway
        elif (c := self.find_challenge(challenge.config.id)) is not None:
            if replace_existing:
                self.remove_challenge(folder=c.repository_path)
            else:
                raise ChallengeExistsError(challenge.config.id, c.repository_path)

        new_challenge_path = self.location / challenge.repository_path

        # Ensure challenge folder exists
        new_challenge_path.mkdir(parents=True, exist_ok=True)

        if preserve_original:
            challenge.copy_to(new_challenge_path, as_subfolder=False)
        else:
            challenge.move_to(new_challenge_path, as_subfolder=False)

    def remove_challenge(
        self,
        *,
        id: str | None = None,
        name: str | None = None,
        folder: str | Path | None = None,
        challenge: Challenge | None = None,
    ) -> None:
        """Removes a challenge from the repository.

        The challenge can be specified by its ID, name, folder path, or as a `Challenge` object.

        Args:
            id (str, optional): The ID of the challenge to remove.
            name (str, optional): The name of the challenge to remove.
            folder (str | Path, optional): The path to the challenge folder to remove.
            challenge (Challenge, optional): The Challenge object to remove.
        """
        if (id, name, folder, challenge).count(None) < 3:
            raise InvalidParameterError(
                "Only one of 'id', 'name', 'folder', or 'challenge' should be specified."
            )

        if id is not None:
            challenge = self.find_challenge(id)
            if challenge is None:
                raise ChallengeNotFoundError(id, "ID")
            folder = self.location / challenge.repository_path
        elif name is not None:
            challenge = self.find_challenge(name)
            if challenge is None:
                raise ChallengeNotFoundError(name, "name")
            folder = self.location / challenge.repository_path
        elif folder is not None:
            if isinstance(folder, str):
                folder = Path(folder)

            # If folder is relative, make it relative to the repo location
            if not folder.is_absolute():
                folder = self.location / folder

            if not folder.is_dir():
                raise PathIsNotDirectoryError(folder.absolute())

            # Safety check, ensure the folder is in the repo
            if folder.resolve().parent.parent != self.challenges_path.resolve():
                raise FolderOutsideRepositoryError(folder.absolute())
        elif challenge is not None:
            folder = self.location / challenge.repository_path
        else:
            raise InvalidParameterError(
                "One of 'id', 'name', 'folder', or 'challenge' must be specified."
            )

        if not folder.exists():
            from ctfa.core.exceptions import ConfigFileNotFoundError

            raise ConfigFileNotFoundError(folder.absolute(), "challenge folder")

        shutil.rmtree(folder)

    # ----------------------------------------------------------------
    # Readme Rendering
    # ----------------------------------------------------------------

    def render_category_readme(self, category: str) -> str:
        """Renders the README for the specified category.

        Args:
            category (str): The category to render the README for.

        Returns:
            str: The rendered README content.
        """
        if category.lower() not in self.ctf_config.categories:
            raise CategoryNotFoundError(category)

        challenges = []
        services = []
        for challenge in self.walk_challenges(category=category, skip_invalid=True):
            challenges.append(challenge.config)
            if challenge.config.services is not None:
                for service in challenge.config.services:
                    services.append((service, challenge.config))

        distribution = calculate_difficulty_distribution(challenges)

        return _render_category_readme(
            category_name=category,
            ctf_config=self.ctf_config,
            distribution=distribution,
            challenges=challenges,
            services=services,
        )

    def render_repository_readme(self) -> str:
        """Renders the README for the repository.

        Returns:
            str: The rendered README content.
        """
        distributions = {}
        challenges = []
        services = []
        for category in self.ctf_config.categories:
            distributions[category] = {}
            for challenge in self.walk_challenges(category=category, skip_invalid=True):
                difficulty = challenge.config.difficulty
                distributions[category][difficulty] = (
                    distributions[category].get(difficulty, 0) + 1
                )
                challenges.append(challenge.config)
                if challenge.config.services is not None:
                    for service in challenge.config.services:
                        services.append((service, challenge.config))

        # Compute total distribution
        distributions["_total"] = {
            difficulty: sum(dist.get(difficulty, 0) for dist in distributions.values())
            for difficulty in self.ctf_config.difficulties
        }

        return _render_repo_readme(
            ctf_config=self.ctf_config,
            distributions=distributions,
            challenges=challenges,
            services=services,
        )

    def save_category_readme(self, category: str) -> None:
        """Saves the README for the specified category to the category's directory.

        Args:
            category (str): The category to save the README for.
        """
        if category.lower() not in self.ctf_config.categories:
            raise CategoryNotFoundError(category)

        readme_content = self.render_category_readme(category)
        category_path = self.get_category_path(category)
        readme_fp = category_path / "README.md"
        readme_fp.write_text(readme_content, encoding="utf-8")

    def save_repository_readme(self) -> None:
        """Saves the README for the repository to the repository's challenge root."""
        readme_content = self.render_repository_readme()
        readme_fp = self.challenges_path / "README.md"
        readme_fp.write_text(readme_content, encoding="utf-8")

    def save_all_readmes(self) -> None:
        """Saves the README for the repository and all categories."""
        self.save_repository_readme()
        for category in self.ctf_config.categories:
            self.save_category_readme(category)
