from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

from ctf_architect.core.constants import SPECIFICATION_VERSION


class Model(BaseModel, validate_assignment=True):
    pass


class Flag(Model):
    """
    Represents a challenge flag.

    Attributes:
      flag (str): The flag string.
      regex (bool, optional): Specifies whether the flag is a regular expression. Defaults to False.
      case_sensitive (bool, optional): Specifies whether the flag is case-sensitive. Defaults to False.
    """

    flag: str
    regex: bool = False
    case_sensitive: bool = True


class Hint(Model):
    """
    Represents a challenge hint.

    Attributes:
      cost (int): The cost of the hint.
      content (str): The content of the hint.
      requirements (list[int], optional): The list of requirements needed to unlock the hint.
    """

    cost: int
    content: str
    requirements: list[int] | None = None


class Service(Model, extra="allow"):
    """
    Represents a service for a challenge.

    Attributes:
      name (str): The name of the service. Must follow the pattern /^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.
      path (Path): The path to the service.
      port (int, optional): The port number for the service. Only allowed to be None if type is "internal".
      type (str): The type of the service. Must be one of "web", "nc", "ssh", "secret", or "internal".
      extras (dict[str, Any], optional): Extra information to be passed to the Docker Compose file.
    """

    name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")]
    path: Path
    port: int | None = None
    type: Literal["web", "nc", "ssh", "secret", "internal"]
    extras: dict[str, Any] | None = None

    # port is only allowed to be none if type is "internal"
    @model_validator(mode="after")
    def validate_port(self) -> Service:
        if self.port is None and self.type != "internal":
            raise ValueError("Port must be specified for non-internal services")
        return self


class Challenge(Model):
    """
    Represents a challenge.

    Attributes:
      author (str): The author of the challenge.
      category (str): The category of the challenge.
      description (str): The description of the challenge.
      difficulty (str): The difficulty of the challenge.
      name (str): The name of the challenge.
      files (list[Path | HttpUrl], optional): The list of files for the challenge.
      requirements (list[str], optional): The list of requirements needed to unlock the challenge.
      extras (dict[str, Any], optional): Extra information for the challenge.
      flags (list[Flag]): The list of flags for the challenge.
      hints (list[Hint], optional): The list of hints for the challenge.
      services (list[Service], optional): The list of services for the challenge.
    """

    author: str
    category: Annotated[str, StringConstraints(to_lower=True)]
    description: str
    difficulty: Annotated[str, StringConstraints(to_lower=True)]
    name: str
    files: list[HttpUrl | Path] | None = None
    requirements: list[str] | None = None
    extras: dict[str, Any] | None = None
    flags: list[Flag]
    hints: list[Hint] | None = None
    services: list[Service] | None = None

    @model_validator(mode="after")
    def validate_folder_name(self) -> Challenge:
        if not self.folder_name:
            raise ValueError(
                f'Invalid challenge name, unable to create a valid folder name for "{self.name}"'
            )
        return self

    @property
    def folder_name(self) -> str:
        """
        Converts the challenge name to an alphanumeric string with spaces,
        dashes, and underscores only that should be supported by Windows and
        Linux filesystems.

        Returns:
          str: The folder name for the challenge.
        """
        return re.sub(r"[^a-zA-Z0-9-_ ]", "", self.name).strip()

    @property
    def full_path(self) -> Path:
        """
        The full path to the challenge folder from the root of the CTF repo.

        Returns:
          Path: The full path to the challenge folder.
        """
        return Path("challenges") / self.category.lower() / self.folder_name


class DifficultyConfig(Model):
    """
    Represents a difficulty configuration for a CTF challenge.

    Attributes:
      name (str): The name of the difficulty level.
      value (int): The value of the difficulty level.
    """

    name: Annotated[str, StringConstraints(to_lower=True)]
    value: int


class CTFConfig(Model):
    """
    Represents the configuration for a CTF.

    Attributes:
      categories (list[str]): The list of categories for the CTF.
      extras (list[str]): The list of extra fields for the CTF.
      starting_port (int): The starting port for the CTF.
      name (str): The name of the CTF.
      difficulties (list[DifficultyConfig]): The list of difficulties for the CTF.
    """

    categories: list[Annotated[str, StringConstraints(to_lower=True)]]
    starting_port: int
    name: str
    extras: list[str] | None = None
    difficulties: list[DifficultyConfig]


class BaseFile(Model):
    """
    Represents a base CTF-Architect config file.

    Attributes:
      version (str): The version of the file.
    """

    version: str

    @field_validator("version")
    def validate_version(cls, value: str) -> str:
        if value != SPECIFICATION_VERSION:
            raise ValueError(
                f'Invalid specification version: "{value}",\
        expected "{SPECIFICATION_VERSION}"'
            )
        return value


class ChallengeFile(BaseFile):
    """
    Represents a chall.toml config file.

    Attributes:
      challenge (Challenge): The challenge object.
    """

    challenge: Challenge

    @classmethod
    def from_challenge(cls, challenge: Challenge) -> ChallengeFile:
        return cls(version=SPECIFICATION_VERSION, challenge=challenge)


class ConfigFile(BaseFile):
    """
    Represents a ctf_config.toml config file.

    Attributes:
      config (CTFConfig): The CTF config object.
    """

    config: CTFConfig

    @classmethod
    def from_ctf_config(cls, config: CTFConfig) -> ConfigFile:
        """
        Creates a ConfigFile object from a CTFConfig object.

        Args:
          config (CTFConfig): The CTFConfig object to convert.

        Returns:
          ConfigFile: The converted ConfigFile object.
        """
        return cls(version=SPECIFICATION_VERSION, config=config)


class ServicePortMapping(Model):
    """
    Represents a port mapping for a challenge service.
    """

    from_port: int
    to_port: int


class PortMappingFile(BaseFile):
    """
    Represents a port_mapping.json file.
    """

    mapping: dict[str, ServicePortMapping]

    @classmethod
    def from_mapping(cls, mapping: dict[str, ServicePortMapping]) -> PortMappingFile:
        return cls(version=SPECIFICATION_VERSION, mapping=mapping)
