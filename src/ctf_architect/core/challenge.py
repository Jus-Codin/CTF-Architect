"""Functions and classes for challenge level operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from tomlkit import comment, document, dump, load, nl

from ctf_architect.constants import CHALLENGE_CONFIG_FILE, CHALLENGE_CONFIG_HEADER
from ctf_architect.core.readme import render_challenge_readme
from ctf_architect.models.challenge import ChallengeConfig, ChallengeFile
from ctf_architect.utils import copy_into, is_challenge_folder
from ctf_architect.version import CHALLENGE_SPEC_VERSION


class Challenge:
    """Represents a challenge folder.

    Warning:
        This class should not be instantiated directly. Use the `Challenge.from_path` method to create an instance.

    Attributes:
        path (Path): The path of the challenge folder
        config (ChallengeConfig): The challenge config defined for the challenge
        initialized (bool): Whether the challenge folder has been initialized.
                            This is set to True when the challenge folder is created or loaded from a config file.
    """

    def __init__(self, path: Path, challenge_config: ChallengeConfig, initialized: bool = False) -> None:
        self.path = path
        self.config = challenge_config
        self.initialized = initialized

    @staticmethod
    def load_config(path: str | Path) -> ChallengeConfig:
        """Loads the challenge config from the specified path.

        If the path is a file, it will be used as the config file.
        Else, it will look for a `chall.toml` file in the folder.

        Args:
            path (str | Path): The path to the challenge config file or folder containing it.

        Returns:
            ChallengeConfig: The challenge config.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = path / CHALLENGE_CONFIG_FILE

        with open(config_fp, encoding="utf-8") as f:
            data = load(f)

        config_file = ChallengeFile.model_validate(data.unwrap())

        return config_file.challenge

    @staticmethod
    def write_config(path: str | Path, challenge_config: ChallengeConfig) -> None:
        """Writes the given challenge config to the specified path.

        If the path is a file, it will be used as the config file.
        Else, it will write the config to a `chall.toml` file in the folder

        Args:
            path (str | Path): The folder or file to write the challenge config to.
            challenge_config (ChallengeConfig): The challenge config to write.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = path / CHALLENGE_CONFIG_FILE

        doc = document()

        for line in CHALLENGE_CONFIG_HEADER.splitlines():
            doc.add(comment(line))
        doc.add(nl())

        doc.add("version", str(CHALLENGE_SPEC_VERSION))  # type: ignore

        # NOTE: We have to do exclude_none=True because pydantic ignores exclude_defaults for fields with
        #       custom field serializers. We need it for `challenge.files`, but it can be None, so we need
        #       to exclude it here. This is fine since None cannot be serialized in TOML anyway.
        #       See: https://github.com/pydantic/pydantic/issues/6575
        doc.add("challenge", challenge_config.model_dump(mode="json", exclude_defaults=True, exclude_none=True))  # type: ignore

        with open(config_fp, "w", encoding="utf-8") as f:
            dump(doc, f)

    @staticmethod
    def write_readme(path: str | Path, challenge_config: ChallengeConfig) -> None:
        """Writes the challenge readme to the specified path.

        If the path is a file, it will be used as the readme file.
        Else, it will write the readme to a `README.md` file in the folder.

        Args:
            path (str | Path): The folder or file to write the challenge readme to.
            challenge_config (ChallengeConfig): The challenge config to generate the readme for.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            readme_fp = path
        else:
            readme_fp = path / "README.md"

        readme_content = render_challenge_readme(challenge_config)

        readme_fp.write_text(readme_content, encoding="utf-8")

    @classmethod
    def from_path(cls, path: str | Path) -> Challenge:
        """Loads a Challenge from the specified path.

        Args:
            path (str | Path): The path to the challenge folder.

        Returns:
            Challenge: The challenge folder instance.
        """
        if isinstance(path, str):
            path = Path(path)

        if not is_challenge_folder(path):
            raise ValueError(f"The specified path {path} is not a valid challenge folder.")

        challenge = cls.load_config(path)

        return cls(path, challenge, initialized=True)

    @property
    def repo_path(self) -> Path:
        """The path to the challenge folder relative to the repository root."""
        return Path("challenges", self.config.category.lower(), self.config.folder_name)

    def copy_to(self, destination: str | Path, as_subfolder: bool = True) -> Challenge:
        """Copies the challenge folder into the specified destination.

        This will create a new folder at the destination path and copy all files from the challenge folder to it.
        If the destination folder already exists and is not empty, an error will be raised.

        Note:
            Only initialized challenges can be copied. If the challenge is not initialized, it will raise an error.

        Args:
            destination (str | Path): The destination path to copy the challenge folder into.
            as_subfolder (bool): Whether to copy the challenge folder as a subfolder inside the destination.
                                 If False, the challenge folder's contents will be copied directly into the destination.

        Returns:
            Challenge: A new Challenge instance pointing to the copied folder.

        Raises:
            FileExistsError: If the destination folder already exists and is not empty.
        """
        if not self.initialized:
            raise RuntimeError("Cannot copy an uninitialized challenge. Please initialize the challenge first.")

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

        return Challenge.from_path(target_folder)

    def move_to(self, destination: str | Path, as_subfolder: bool = True) -> Challenge:
        """Moves the challenge folder to the specified destination.

        This will move the entire challenge folder to the new location, including all files and subdirectories.

        Note:
            Only initialized challenges can be moved. If the challenge is not initialized, it will raise an

        Args:
            destination (str | Path): The destination path to move the challenge folder to.
            as_subfolder (bool): Whether to move the challenge folder as a subfolder inside the destination.
                                 If False, the challenge folder will be moved directly into the destination.

        Returns:
            Challenge: A new Challenge instance pointing to the moved folder.
        """
        if not self.initialized:
            raise RuntimeError("Cannot move an uninitialized challenge. Please initialize the challenge first.")

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

        if as_subfolder:
            shutil.move(self.path, target_folder)
        else:
            for file in self.path.iterdir():
                shutil.move(file, target_folder / file.name)

        return Challenge.from_path(target_folder)

    def save_config(self) -> None:
        """Saves the challenge config to the folder."""
        self.write_config(self.path, self.config)

    def save_readme(self) -> None:
        """Writes the challenge readme to the folder."""
        self.write_readme(self.path, self.config)

    def save_all(self) -> None:
        """Saves both the challenge config and readme to the folder."""
        self.save_config()
        self.save_readme()

    def refresh(self) -> None:
        """Refreshes the challenge config from the folder."""
        if not self.initialized:
            raise RuntimeError("Cannot refresh an uninitialized challenge. Please initialize the challenge first.")

        self.config = self.load_config(self.path)

    @classmethod
    def new(
        cls,
        path: str | Path,
        challenge_config: ChallengeConfig,
        extra_files: list[tuple[str | Path, str | Path]] | None = None,
        as_subfolder: bool = True,
    ) -> Challenge:
        """Creates a new challenge folder at the specified path.

        NOTE: This function does not create the src and solution paths defined in the specification, as they are not actually
              managed by the API. You should specify them in the extra_files argument.

        Args:
            path (str | Path): The path to create the challenge folder at.
            challenge_config (ChallengeConfig): The challenge config to use for the new challenge.
            extra_files (list[tuple[str | Path, str | Path]], optional): A list of tuples mapping source paths to destination paths for extra files or directories to include in the challenge.
                                                                         For security reasons, the destination path must be a relative path that resolves to a subdirectory within the challenge folder.
            as_subfolder (bool, optional): Whether to create the challenge as a subfolder inside the specified path. Otherwise, the challenge will be created at the specified path directly.

        Returns:
            Challenge: A new Challenge instance pointing to the created folder.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            raise NotADirectoryError(f'"{path.absolute()}" is not a directory')

        # Prepare the target path for challenge initialization
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        # To ensure atomicity, we perform all our operations in a tempdir
        # and then move the tempdir to the final location
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if challenge_config.files is not None:
                _dist_files = []

                for dist_file in challenge_config.files:
                    if isinstance(dist_file, Path):
                        # Validate the file
                        if not dist_file.exists():
                            raise FileNotFoundError(f"The file {dist_file.absolute()} does not exist.")

                        if not dist_file.is_file():
                            raise FileNotFoundError(f"The file {dist_file.absolute()} is not a valid file.")

                        # Create the dist folder if it doesn't exist
                        if not (temp_path / "dist").exists():
                            (temp_path / "dist").mkdir()

                        shutil.copy(dist_file, temp_path / "dist")

                        # We need to change the file path to one relative to the folder root
                        _dist_files.append((temp_path / "dist" / dist_file.name).relative_to(temp_path))
                    else:
                        # Just append if it's a URL
                        _dist_files.append(dist_file)

                challenge_config.files = _dist_files

            if challenge_config.services is not None:
                (temp_path / "services").mkdir()

                for service in challenge_config.services:
                    if not service.path.exists():
                        raise FileNotFoundError(f"The service file {service.path.absolute()} does not exist.")

                    if not service.path.is_dir():
                        raise NotADirectoryError(f"The service file {service.path.absolute()} is not a directory.")

                    # Copy the service files to the temp directory
                    shutil.copytree(service.path, temp_path / "services" / service.name)

                    # Update the service path
                    service.path = (temp_path / "services" / service.name).relative_to(temp_path)

            if extra_files is not None:
                copy_into(temp_path, extra_files)

            chall = cls(temp_path, challenge_config, initialized=True)
            chall.save_all()

            return chall.move_to(path, as_subfolder=as_subfolder)
