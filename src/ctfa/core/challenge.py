from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from ruamel.yaml.comments import CommentedMap

from ctfa.constants import CHALLENGE_CONFIG_FILE, CHALLENGE_CONFIG_HEADER, CHALLENGE_SPEC_VERSION
from ctfa.core.exceptions import (
    ChallengePathExistsError,
    ConfigFileNotFoundError,
    DestinationExistsError,
    FileNotFoundInChallengeError,
    InvalidChallengeFolderError,
    InvalidFileTypeError,
)
from ctfa.core.render import render_challenge_readme
from ctfa.models.challenge import ChallengeConfig, ChallengeConfigFile
from ctfa.utils import FileStructureDict, build_file_structure, get_challenge_config_file, is_challenge_folder, yaml


class Challenge:
    """Represents a challenge.

    Attributes:
        location (Path): The path to the challenge folder.
        config (ChallengeConfig): The challenge configuration.
    """

    def __init__(self, challenge_path: Path, challenge_config: ChallengeConfig) -> None:
        self.location = challenge_path.resolve()
        self.config = challenge_config

    @property
    def repository_path(self) -> Path:
        """The path to the challenge folder relative to the repository root."""
        return Path("challenges") / self.config.category / self.config.folder_name

    @staticmethod
    def load_config_file(path: str | Path) -> ChallengeConfig:
        """Loads a ChallengeConfigFile from the specified path.

        If the path specified is a file, it will load the config from that file directly.
        Else, it will look for the challenge config file in the specified directory.

        Args:
            path (str | Path): The path to the challenge config file or directory.

        Returns:
            ChallengeConfig: The loaded ChallengeConfig object.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = get_challenge_config_file(path)
            if config_fp is None:
                raise ConfigFileNotFoundError(path, "challenge config")

        with config_fp.open(encoding="utf-8") as f:
            data = yaml.load(f)

        config_file = ChallengeConfigFile.model_validate(data)

        return config_file.challenge

    @staticmethod
    def dump_config_file(path: str | Path, challenge_config: ChallengeConfig) -> None:
        """Dumps a ChallengeConfigFile to an existing file or to a challenge directory.

        If the path specified is an existing file, it will dump the config in the file directly.
        Else, it will dump the config file in the specified directory.

        Args:
            path (str | Path): The path to dump the challenge config file to.
            challenge_config (ChallengeConfig): The ChallengeConfig object to dump.
        """
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_fp = path
        else:
            config_fp = path / CHALLENGE_CONFIG_FILE

        # Create the YAML document with headers and spacing

        # NOTE: We have to do exclude_none=True because pydantic ignores exclude_defaults for fields with
        #       custom field or model serializers. We need it for `challenge.files`, but it can be None,
        #       so we need to exclude it here.
        #       See: https://github.com/pydantic/pydantic/issues/6575
        challenge_data = CommentedMap(
            challenge_config.model_dump(mode="json", exclude_defaults=True, exclude_none=True)
        )

        # Add spacing between top-level dict or list keys
        for key in challenge_data.keys():
            if isinstance(challenge_data[key], list | dict):
                challenge_data.yaml_set_comment_before_after_key(key, before="\n")

        file_data = CommentedMap(
            {
                "version": str(CHALLENGE_SPEC_VERSION),
                "challenge": challenge_data,
            }
        )

        # Add header comment
        file_data.yaml_set_start_comment(CHALLENGE_CONFIG_HEADER + "\n")

        # Add spacing before "challenge" key
        file_data.yaml_set_comment_before_after_key("challenge", before="\n")

        with config_fp.open("w", encoding="utf-8") as f:
            yaml.dump(file_data, f)

    @staticmethod
    def dump_readme(path: str | Path, challenge_config: ChallengeConfig) -> None:
        """Dumps the README.md file for a challenge.

        If the path specified is an existing file, it will dump the README.md file in the file directly.
        Else, it will dump the README.md file in the specified directory.

        Args:
            path (str | Path): The path to the challenge directory or file to dump to.
            challenge_config (ChallengeConfig): The ChallengeConfig object to render the README for.
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
    def load_folder(cls, challenge_path: str | Path) -> Challenge:
        """Loads a Challenge from the specified folder path.

        Args:
            challenge_path (str | Path): The path to the challenge folder.

        Returns:
            Challenge: The challenge folder instance.
        """
        if isinstance(challenge_path, str):
            challenge_path = Path(challenge_path)

        if not is_challenge_folder(challenge_path):
            raise InvalidChallengeFolderError(challenge_path)

        challenge_config = cls.load_config_file(challenge_path)

        return cls(challenge_path, challenge_config)

    @classmethod
    def _unsafe_package(
        cls,
        challenge_config: ChallengeConfig,
        output_path: Path,
        extra_files: FileStructureDict | None = None,
    ) -> Challenge:
        """Packages a Challenge into a folder at the specified output path directly.

        WARNING: This method does not ensure atomicity and may leave partial files if interrupted.

        This function should only be used in controlled environments or in a temporary directory.
        If you want to package a challenge safely, use `Challenge.package()` instead.

        Args:
            challenge_config (ChallengeConfig): The challenge configuration.
            output_path (Path): The path to output the packaged challenge.
            extra_files (FileStructureDict | None): Additional files to include in the challenge package.

        Returns:
            Challenge: The packaged Challenge instance.
        """
        # Check if output path is an existing file
        # TOCTOU is pretty bad here, but this function is meant to be unsafe anyway.
        if output_path.exists() and output_path.is_file():
            raise ChallengePathExistsError(output_path)
        else:
            output_path.mkdir(parents=True, exist_ok=True)

        # Create copy of challenge config to modify paths
        new_challenge_config = challenge_config.model_copy(deep=True)

        file_structure: FileStructureDict = {}

        # Add in extra files if provided
        # For now, we don't allow extra files to overwrite dist/ or services/ folders
        # Maybe a future TODO?
        if extra_files:
            file_structure.update(extra_files)

        # Prepare static files
        if new_challenge_config.files is not None:
            file_structure["dist"] = {}
            for dist_file in new_challenge_config.files:
                if dist_file.type == "static":
                    # Validate the file
                    if not dist_file.path.exists():
                        raise FileNotFoundInChallengeError(dist_file.path, "static file")
                    if not dist_file.path.is_file():
                        raise InvalidFileTypeError(dist_file.path, "file")

                    # Update the file's path to be relative to the challenge root
                    src_path = dist_file.path
                    dist_file.path = Path("dist") / src_path.name

                    # Add to file structure
                    file_structure["dist"][src_path.name] = str(src_path.resolve())  # pyright: ignore[reportIndexIssue]

        # Prepare service folders
        if new_challenge_config.services is not None:
            file_structure["services"] = {}
            for service in new_challenge_config.services:
                # Validate the service folder
                if not service.path.exists():
                    raise FileNotFoundInChallengeError(service.path, "service folder")

                if not service.path.is_dir():
                    raise InvalidFileTypeError(service.path, "directory")

                # Update the service's path to be relative to the challenge root
                src_path = service.path
                service.path = Path("services") / src_path.name

                # Add to file structure
                file_structure["services"][src_path.name] = str(src_path.resolve())  # pyright: ignore[reportIndexIssue]

        # Build the file structure in the temp directory
        build_file_structure(file_structure, output_path)

        # Dump the challenge config and README file
        cls.dump_config_file(output_path, new_challenge_config)
        cls.dump_readme(output_path, new_challenge_config)
        return cls.load_folder(output_path)

    @classmethod
    def package(
        cls,
        challenge_config: ChallengeConfig,
        output_path: str | Path,
        extra_files: FileStructureDict | None = None,
        as_subfolder: bool = True,
    ) -> Challenge:
        """Packages a Challenge into a folder at the specified output path.

        Args:
            challenge_config (ChallengeConfig): The challenge configuration.
            output_path (str | Path): The path to output the packaged challenge.
            extra_files (FileStructureDict | None): Additional files to include in the challenge package.
            as_subfolder (bool): Whether to create the challenge as a subfolder using the folder_name.

        Returns:
            Challenge: The packaged Challenge instance.
        """
        if isinstance(output_path, str):
            output_path = Path(output_path)

        if as_subfolder:
            challenge_path = output_path / challenge_config.folder_name
        else:
            challenge_path = output_path

        # Prepare target path for challenge initialization
        # TOCTOU is pretty bad here, but we're doing stuff in a temp folder later anyway
        # so if it fails later, it's not a big deal.
        if challenge_path.exists():
            if challenge_path.is_file():
                raise ChallengePathExistsError(challenge_path)
        else:
            challenge_path.mkdir(parents=True, exist_ok=True)

        # To ensure atomicity, we perform all our ouperations in a temp folder
        # and then move the packaged challenge to the final location.
        with TemporaryDirectory(prefix="ctfa_") as temp_dir:
            temp_path = Path(temp_dir)

            # Package the challenge in the temp folder
            temp_challenge = cls._unsafe_package(
                challenge_config,
                temp_path,
                extra_files=extra_files,
            )

            # Move the temp challenge to the final location
            temp_challenge.move_to(challenge_path, as_subfolder=False)

        # We could technically return temp_challenge here, but it would be safer
        # to reload from the final location
        return cls.load_folder(challenge_path)

    def copy_to(self, destination: str | Path, as_subfolder: bool = True) -> Challenge:
        """Copies the Challenge to a the specified destination.

        Args:
            destination (str | Path): The path to copy the challenge to.
            as_subfolder (bool): Whether to copy the challenge as a subfolder using the folder_name.

        Returns:
            Challenge: The copied Challenge instance.
        """
        if isinstance(destination, str):
            destination = Path(destination)

        if as_subfolder:
            # If true, create a subfolder with the challenge's folder name
            new_challenge_path = destination / self.config.folder_name
        else:
            # else, copy directly to the specified destination
            new_challenge_path = destination

        if new_challenge_path.exists():
            if not new_challenge_path.is_dir():
                raise DestinationExistsError(new_challenge_path, "is an existing file")

            if any(new_challenge_path.iterdir()):
                raise DestinationExistsError(new_challenge_path, "is not empty")

        shutil.copytree(self.location, new_challenge_path, dirs_exist_ok=True)

        return Challenge.load_folder(new_challenge_path)

    def move_to(self, destination: str | Path, as_subfolder: bool = True) -> None:
        """Moves the Challenge to a the specified destination.

        Note: This function will edit the Challenge's location in place.

        Args:
            destination (str | Path): The path to move the challenge to.
            as_subfolder (bool): Whether to move the challenge as a subfolder using the folder_name.
        """
        if isinstance(destination, str):
            destination = Path(destination)

        if as_subfolder:
            # If true, create a subfolder with the challenge's folder name
            new_challenge_path = destination / self.config.folder_name
        else:
            # else, move directly to the specified destination
            new_challenge_path = destination

        if new_challenge_path.exists():
            if not new_challenge_path.is_dir():
                raise DestinationExistsError(new_challenge_path, "is an existing file")

            if any(new_challenge_path.iterdir()):
                raise DestinationExistsError(new_challenge_path, "is not empty")

        if as_subfolder:
            shutil.move(self.location, new_challenge_path)
        else:
            for item in self.location.iterdir():
                shutil.move(item, new_challenge_path / item.name)

        self.location = new_challenge_path

    def reload(self) -> None:
        """Reloads the Challenge's configuration from its config file."""
        self.config = self.load_config_file(self.location)

    def save_config(self) -> None:
        """Saves the Challenge's configuration to its config file."""
        self.dump_config_file(self.location, self.config)

    def save_readme(self) -> None:
        """Saves the Challenge's README.md file."""
        self.dump_readme(self.location, self.config)

    def save(self) -> None:
        """Saves the Challenge's configuration and README.md file."""
        self.save_config()
        self.save_readme()
