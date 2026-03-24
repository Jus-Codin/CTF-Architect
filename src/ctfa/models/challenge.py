from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import (
    Field,
    HttpUrl,
    SerializerFunctionWrapHandler,
    StringConstraints,
    field_serializer,
    field_validator,
    model_validator,
)

from ctfa.models._base import Model, SlugStr
from ctfa.version import CHALLENGE_SPEC_VERSION, is_supported_challenge_version


class StaticFile(Model):
    """Represents a static file for a challenge.

    Attributes:
        path (Path): The path to the static file.
    """

    type: Literal["static"] = "static"
    path: Path

    @field_serializer("type", mode="wrap")
    def _force_include_type(self, type: str, handler: SerializerFunctionWrapHandler) -> str:
        # Extremely hacky way to force inclusion of the "type" field even when
        # `exclude_defaults=True` is used during serialization.
        # See https://github.com/pydantic/pydantic/discussions/9108
        # and https://github.com/pydantic/pydantic/issues/6575
        return handler(type)

    @field_serializer("path")
    def _serialize_path(self, path: Path) -> str:
        return path.as_posix()


class URLFile(Model):
    """Represents a URL file for a challenge.

    Attributes:
        url (HttpUrl): The URL where the file can be accessed.
    """

    type: Literal["url"] = "url"
    url: HttpUrl

    @field_serializer("type", mode="wrap")
    def _force_include_type(self, type: str, handler: SerializerFunctionWrapHandler) -> str:
        # Extremely hacky way to force inclusion of the "type" field even when
        # `exclude_defaults=True` is used during serialization.
        # See https://github.com/pydantic/pydantic/discussions/9108
        # and https://github.com/pydantic/pydantic/issues/6575
        return handler(type)

    @field_serializer("url")
    def _serialize_url(self, url: HttpUrl) -> str:
        return str(url)


# TODO: Support plugin-defined file types using callable discriminators
ChallengeFile = Annotated[StaticFile | URLFile, Field(discriminator="type")]


class StaticFlag(Model):
    """Represents a static flag for a challenge.

    Attributes:
        value (str): The static flag value.
        case_sensitive (bool, optional): Specifies whether the flag is case-sensitive. Defaults to True.
    """

    type: Literal["static"] = "static"
    value: str
    case_sensitive: bool = True

    @field_serializer("type", mode="wrap")
    def _force_include_type(self, type: str, handler: SerializerFunctionWrapHandler) -> str:
        # Extremely hacky way to force inclusion of the "type" field even when
        # `exclude_defaults=True` is used during serialization.
        # See https://github.com/pydantic/pydantic/discussions/9108
        # and https://github.com/pydantic/pydantic/issues/6575
        return handler(type)


class RegexFlag(Model):
    """Represents a regex flag for a challenge.

    Attributes:
        pattern (str): The regex pattern for the flag.
    """

    type: Literal["regex"] = "regex"
    pattern: str

    @field_serializer("type", mode="wrap")
    def _force_include_type(self, type: str, handler: SerializerFunctionWrapHandler) -> str:
        # Extremely hacky way to force inclusion of the "type" field even when
        # `exclude_defaults=True` is used during serialization.
        # See https://github.com/pydantic/pydantic/discussions/9108
        # and https://github.com/pydantic/pydantic/issues/6575
        return handler(type)


ChallengeFlag = Annotated[StaticFlag | RegexFlag, Field(discriminator="type")]


class ChallengeHint(Model):
    """Represents a hint for a challenge.

    Attributes:
        cost (int): The cost of the hint.
        content (str): The content of the hint.
        requirements (list[int], optional): The list of requirements needed to unlock the hint.
    """

    cost: int
    content: str
    requirements: list[int] | None = None


PortInt: TypeAlias = Annotated[int, Field(ge=1, le=65535)]


class ChallengeService(Model):
    """Represents a challenge service.

    Attributes:
        type (Literal["web", "tcp", "ssh", "secret", "internal"]): The type of the service.
        name (SlugStr): The name of the service.
        path (Path): The path to the service.
        ports (list[int]): The list of ports of the service. Allowed to be unspecified if the service is internal.
        networks (list[SlugStr], optional): The list of networks the service is connected to. Defaults to None.
        annotations (dict[str, Any], optional): The extra information about the service to be passed to the docker compose file. Defaults to None.
    """

    type: Literal["web", "tcp", "ssh", "secret", "internal"]
    name: SlugStr
    path: Path
    ports: Annotated[list[PortInt], Field(default_factory=list)]
    networks: list[SlugStr] | None = None
    annotations: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_ports(self) -> ChallengeService:
        if not self.ports and self.type != "internal":
            raise ValueError("Ports must be specified for non-internal services")

        return self

    @field_serializer("path")
    def _serialize_path(self, path: Path) -> str:
        return path.as_posix()

    def unique_name(self, challenge: ChallengeConfig) -> str:
        return f"{challenge.category}-{challenge.id}-{self.name}".lower().replace(" ", "-")


class ChallengeNetworkConfig(Model):
    """Represents a challenge network.

    Attributes:
        internal (bool): Specifies whether the network is internal.
    """

    internal: bool


class ChallengeConfig(Model):
    """Represents a challenge configuration.

    Attributes:
        id (SlugStr): The unique identifier for the challenge.
        name (str): The name of the challenge.
        description (str): The description of the challenge.
        category (str): The category of the challenge.
        difficulty (str): The difficulty level of the challenge.
        author (str): The author of the challenge.
        folder_name (str): The folder name for the challenge. If not specified, defaults to a sanitized version of the name or the ID.
        requirements (list[SlugStr], optional): A list of challenge IDs that must be solved before this challenge can be unlocked.
        files (list[ChallengeFile], optional): The list of files associated with the challenge.
        flags (list[ChallengeFlag], optional): The list of flags for the challenge.
        hints (list[ChallengeHint], optional): The list of hints for the challenge.
        extra_labels (dict[str, str | int | float | bool], optional): Extra labels for the challenge.
        annotations (dict[str, Any], optional): Annotations for the challenge.
        services (list[ChallengeService], optional): The list of services for the challenge.
        networks (dict[SlugStr, ChallengeNetworkConfig], optional): The network configurations for the challenge's services.
    """

    id: SlugStr
    name: str
    description: str
    category: Annotated[str, StringConstraints(to_lower=True, min_length=1, pattern="^[a-zA-Z][a-zA-Z0-9 _-]*$")]
    difficulty: Annotated[str, StringConstraints(to_lower=True, min_length=1)]
    author: str
    folder_name: Annotated[str, StringConstraints(min_length=1, pattern="^[a-zA-Z0-9][a-zA-Z0-9 _-]*$")] = None  # type: ignore
    requirements: Annotated[list[SlugStr], Field(min_length=1)] | None = None
    files: Annotated[list[ChallengeFile], Field(min_length=1)] | None = None
    flags: Annotated[list[ChallengeFlag], Field(min_length=1)] | None = None
    hints: Annotated[list[ChallengeHint], Field(min_length=1)] | None = None
    extra_labels: Annotated[dict[str, str | int | float | bool], Field(min_length=1)] | None = None
    annotations: Annotated[dict[str, Any], Field(min_length=1)] | None = None
    services: Annotated[list[ChallengeService], Field(min_length=1)] | None = None
    networks: Annotated[dict[SlugStr, ChallengeNetworkConfig], Field(min_length=1)] | None = None

    @model_validator(mode="after")
    def _ensure_folder_name(self) -> ChallengeConfig:
        if not self.folder_name:
            sanitized = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9 _-]", "", self.name).strip()
            if not sanitized:
                sanitized = self.id
            self.folder_name = sanitized
        return self

    @property
    def default_network_name(self) -> str:
        """The default network name for the challenge."""
        return f"{self.category}-{self.id}-default".lower().replace(" ", "-")

    @property
    def repository_path(self) -> Path:
        """The repository path for the challenge."""
        return Path("challenges") / self.category.lower() / self.folder_name


class ChallengeConfigFile(Model):
    """Represents a challenge config file.

    Attributes:
        version (str): The specification version.
        challenge (ChallengeConfig): The challenge config object.
    """

    version: str
    challenge: ChallengeConfig

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_challenge_version(value):
            raise ValueError(
                f'Unsupported Challenge specification version: "{value}", current version "{CHALLENGE_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_challenge(cls, challenge: ChallengeConfig) -> ChallengeConfigFile:
        """Creates a ChallengeConfigFile from a ChallengeConfig.

        Args:
            challenge (ChallengeConfig): The challenge config object.

        Returns:
            ChallengeConfigFile: The created ChallengeConfigFile object.
        """
        return cls(version=str(CHALLENGE_SPEC_VERSION), challenge=challenge)
