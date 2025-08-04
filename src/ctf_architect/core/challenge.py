"""Functions and classes for challenge level operations."""

from __future__ import annotations

import shutil
from pathlib import Path

from tomlkit import comment, document, dump, load, nl

from ctf_architect.constants import CHALLENGE_CONFIG_FILE, CHALLENGE_CONFIG_HEADER
from ctf_architect.models.challenge import ChallengeConfig, ChallengeFile
from ctf_architect.version import CHALLENGE_SPEC_VERSION


def is_challenge_folder(path: str | Path) -> bool:
    """Checks if the specified folder is a challenge folder.

    If it has a Challenge Config file, it is considered a challenge folder.

    Args:
        path (str | Path): The path to the folder to check.

    Returns:
        bool: True if the folder is a challenge folder, False otherwise.
    """
    for file in Path(path).iterdir():
        if file.name.lower() == CHALLENGE_CONFIG_FILE:
            return True

    return False


def load_chall_config(path: str | Path) -> ChallengeConfig:
    """Loads the challenge config from the specified path.

    Args:
        path (str | Path): The path to the challenge config file.

    Returns:
        Challenge: The challenge config.
    """
    if isinstance(path, str):
        path = Path(path)

    with open(path / CHALLENGE_CONFIG_FILE, encoding="utf-8") as f:
        data = load(f)

    config_file = ChallengeFile.model_validate(data.unwrap())

    return config_file.challenge


def write_chall_config(path: str | Path, challenge: ChallengeConfig) -> None:
    """Writes the given challenge config to the specified path.

    Args:
        path (str | Path): The folder to write the challenge config to.
        challenge (Challenge): The challenge config to write.
    """
    if isinstance(path, str):
        path = Path(path)

    doc = document()

    for line in CHALLENGE_CONFIG_HEADER.splitlines():
        doc.add(comment(line))
    doc.add(nl())

    doc.add("version", str(CHALLENGE_SPEC_VERSION))  # type: ignore

    # NOTE: We have to do exclude_none=True because pydantic ignores exclude_defaults for fields with
    #       custom field serializers. We need it for `challenge.files`, but it can be None, so we need
    #       to exclude it here. This is fine since None cannot be serialized in TOML anyway.
    #       See: https://github.com/pydantic/pydantic/issues/6575
    doc.add("challenge", challenge.model_dump(mode="json", exclude_defaults=True, exclude_none=True))  # type: ignore

    with open(path / CHALLENGE_CONFIG_FILE, "w", encoding="utf-8") as f:
        dump(doc, f)


def write_chall_readme(path: str | Path, challenge: ChallengeConfig) -> None:
    """Writes the challenge readme to the specified path.

    Args:
        path (str | Path): The folder to write the challenge readme to.
        challenge: (Challenge): The challenge config to generate the readme for.
    """
    if isinstance(path, str):
        path = Path(path)

    (path / "README.md").write_text(challenge.readme, encoding="utf-8")


class ChallengeFolder:
    """Represents a challenge folder.

    Attributes:
        path (Path): The path of the challenge folder
        config (Challenge): The challenge config defined for the challenge
    """

    def __init__(self, path: Path, challenge_config: ChallengeConfig):
        self.path = path
        self.config = challenge_config

    @classmethod
    def from_path(cls, path: str | Path) -> ChallengeFolder:
        """Loads a ChallengeFolder from the specified path.

        Args:
            path (str | Path): The path to the challenge folder.

        Returns:
            ChallengeFolder: The challenge folder instance.
        """
        if isinstance(path, str):
            path = Path(path)

        if not is_challenge_folder(path):
            raise ValueError(f"The specified path {path} is not a valid challenge folder.")

        challenge = load_chall_config(path)

        return cls(path, challenge)

    def copy_to(self, destination: str | Path, as_subfolder: bool = True) -> ChallengeFolder:
        """Copies the challenge folder into the specified destination.

        This will create a new folder at the destination path and copy all files from the challenge folder to it.
        If the destination folder already exists and is not empty, an error will be raised.

        Args:
            destination (str | Path): The destination path to copy the challenge folder into.
            as_subfolder (bool): Whether to copy the challenge folder as a subfolder inside the destination.
                                 If False, the challenge folder's contents will be copied directly into the destination.

        Returns:
            ChallengeFolder: A new ChallengeFolder instance pointing to the copied folder.

        Raises:
            FileExistsError: If the destination folder already exists and is not empty.
        """
        if isinstance(destination, str):
            destination = Path(destination)

        if as_subfolder:
            # If as_subfolder is True, we create a subfolder with the challenge's folder name.
            target_folder = destination / self.config.folder_name
        else:
            # If as_subfolder is False, we copy the contents directly into the destination.
            target_folder = destination

        if target_folder.exists():
            # Ensure the target path is a directory.
            if not target_folder.is_dir():
                raise NotADirectoryError(f"The destination {target_folder} is not a directory.")

            # If there are files in the target folder, we error out to prevent data loss.
            # else, we can safely copy into it.
            if any(target_folder.iterdir()):
                raise FileExistsError(f"The destination folder {target_folder} already exists and is not empty.")

        shutil.copytree(self.path, target_folder, dirs_exist_ok=True)

        return ChallengeFolder(target_folder, self.config)

    def move_to(self, destination: str | Path, as_subfolder: bool = True) -> ChallengeFolder:
        """Moves the challenge folder to the specified destination.

        This will move the entire challenge folder to the new location, including all files and subdirectories.

        Args:
            destination (str | Path): The destination path to move the challenge folder to.
            as_subfolder (bool): Whether to move the challenge folder as a subfolder inside the destination.
                                 If False, the challenge folder will be moved directly into the destination.

        Returns:
            ChallengeFolder: A new ChallengeFolder instance pointing to the moved folder.
        """
        if isinstance(destination, str):
            destination = Path(destination)

        if as_subfolder:
            # If as_subfolder is True, we create a subfolder with the challenge's folder name.
            target_folder = destination / self.config.folder_name
        else:
            # If as_subfolder is False, we move the challenge folder directly into the destination.
            target_folder = destination

        if target_folder.exists():
            # Ensure the target path is a directory.
            if not target_folder.is_dir():
                raise NotADirectoryError(f"The destination {target_folder} is not a directory.")

            # If there are files in the target folder, we error out to prevent data loss.
            if any(target_folder.iterdir()):
                raise FileExistsError(f"The destination folder {target_folder} already exists and is not empty.")

        shutil.move(self.path, target_folder)

        return ChallengeFolder(target_folder, self.config)

    def save_config(self) -> None:
        """Saves the challenge config to the folder."""
        write_chall_config(self.path, self.config)

    def save_readme(self) -> None:
        """Writes the challenge readme to the folder."""
        write_chall_readme(self.path, self.config)

    def save_all(self) -> None:
        """Saves both the challenge config and readme to the folder."""
        self.save_config()
        self.save_readme()

    def refresh(self) -> None:
        """Refreshes the challenge config from the folder."""
        self.config = load_chall_config(self.path)
