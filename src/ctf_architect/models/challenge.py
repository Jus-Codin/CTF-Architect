from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    Field,
    HttpUrl,
    StringConstraints,
    field_serializer,
    field_validator,
    model_validator,
)

from ctf_architect.constants import CHALL_README_TEMPLATE
from ctf_architect.models.base import Model
from ctf_architect.version import CHALLENGE_SPEC_VERSION, is_supported_challenge_version


class Flag(Model):
    """Represents a challenge flag.

    Attributes:
        flag (str): The flag string.
        regex (bool, optional): Specifies whether the flag is a regular expression. Defaults to False.
        case_insensitive (bool, optional): Specifies whether the flag is case-insensitive. Defaults to False.
    """

    flag: str
    regex: bool = False
    case_insensitive: bool = False


class Hint(Model):
    """Represents a challenge hint.

    Attributes:
        cost (int): The cost of the hint.
        content (str): The content of the hint.
        requirements (list[int], optional): The list of requirements needed to unlock the hint.
    """

    cost: int
    content: str
    requirements: list[int] | None = None


PortInt = Annotated[int, Field(ge=1, le=65535)]


class Service(Model):
    """Represents a challenge service.

    Attributes:
        name (str): The name of the service.
        path (Path): The path to the service.
        port (int, optional): The port of the service. Allowed to be unspecified if the service is internal or `ports` is specified.
        ports (list[int], optional): The list of ports of the service. Allowed to be unspecified if the service is internal or `port` is specified.
        type (Literal["web", "tcp", "ssh", "secret", "internal"]): The type of the service.
        extras (dict[str, Any], optional): The extra information about the service to be passed to the docker compose file. Defaults to None.
    """

    name: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*$")]
    path: Path
    port: PortInt | None = None
    ports: Annotated[list[PortInt], Field(min_length=1)] | None = None
    type: Literal["web", "tcp", "ssh", "secret", "internal"]
    extras: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_port(self) -> Service:
        if self.port is not None and self.ports is not None:
            raise ValueError("Port and ports cannot both be specified")

        if self.port is None and self.ports is None and self.type != "internal":
            raise ValueError("Port or ports must be specified for non-internal services")

        if self.ports is None:
            self.ports = [self.port]  # type: ignore

        return self

    @field_serializer("path")
    def _serialize_path(self, path: Path) -> str:
        return path.as_posix()

    @property
    def ports_list(self) -> list[PortInt]:
        """The list of ports for the service.

        Returns:
            list[int]: The list of ports for the service.
        """
        # TODO: remove this method and use `self.ports` directly
        return self.ports or [self.port]  # type: ignore

    def unique_name(self, challenge: Challenge) -> str:
        return f"{challenge.category}-{challenge.folder_name}-{self.name}".lower().replace(" ", "-")


class Challenge(Model):
    """Represents a challenge.

    Attributes:
        author (str): The author of the challenge.
        category (str): The category of the challenge.
        description (str): The description of the challenge.
        difficulty (str): The difficulty of the challenge.
        name (str): The name of the challenge.
        folder_name (str, optional): The folder name for the challenge. Must follow the pattern `/^[a-zA-Z][a-zA-Z0-9 _-]*$/`. If not provided, it will be generated from the challenge name.
        files (list[Path | HttpUrl], optional): The list of files for the challenge.
        requirements (list[str], optional): The list of requirements needed to unlock the challenge.
        extras (dict[str, str | int | float | bool], optional): Extra information for the challenge.
        flags (list[Flag]): The list of flags for the challenge.
        hints (list[Hint], optional): The list of hints for the challenge.
        services (list[Service], optional): The list of services for the challenge.
    """

    author: str
    category: Annotated[str, StringConstraints(to_lower=True)]
    description: str
    difficulty: Annotated[str, StringConstraints(to_lower=True)]
    name: str
    folder_name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z][a-zA-Z0-9 _-]*$")] = None  # type: ignore
    files: Annotated[list[HttpUrl | Path], Field(min_length=1)] | None = None
    requirements: Annotated[list[str], Field(min_length=1)] | None = None
    extras: dict[str, str | int | float | bool] | None = None
    flags: Annotated[list[Flag], Field(min_length=1)] | None = None
    hints: Annotated[list[Hint], Field(min_length=1)] | None = None
    services: Annotated[list[Service], Field(min_length=1)] | None = None

    @model_validator(mode="after")
    def _ensure_folder_name(self) -> Challenge:
        if not self.folder_name:
            sanitized = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", self.name).strip()
            if not sanitized:
                raise ValueError(f'Invalid challenge name, unable to create a valid folder name for "{self.name}"')
            self.folder_name = sanitized
        return self

    @field_serializer("files")
    def _serialize_files(self, files: list[HttpUrl | Path]) -> list[str]:
        return [
            file.as_posix() if isinstance(file, Path) else str(file) for file in files
        ]

    @property
    def network_name(self) -> str:
        return f"{self.category}-{self.folder_name}-network".lower().replace(" ", "-")

    @property
    def repo_path(self) -> Path:
        """The path to the challenge folder relative to the repository root."""
        return Path("challenges") / self.category.lower() / self.folder_name

    @property
    def readme(self) -> str:
        """The README content for the challenge."""
        if self.extras is None:
            extras = ""
        else:
            extras = "\n".join(f"- **{key.capitalize()}:** {value}" for key, value in self.extras.items())

        if self.hints is None:
            hints = "None"
        else:
            hints = "\n".join(f"- `{hint.content}` ({hint.cost} points)" for hint in self.hints)

        if self.files is None:
            files = "None"
        else:
            files = ""
            for file in self.files:
                if isinstance(file, Path):
                    files += f"- [{file.name}](<{file.as_posix()}>)\n"
                else:
                    files += f"- {file}\n"
            files = files.strip()

        if self.flags is None:
            flags = "None"
        else:
            flags = "\n".join(
                f"- `{flag.flag}` ({'regex' if flag.regex else 'static'}, {'case-insensitive' if flag.case_insensitive else 'case-sensitive'})"
                for flag in self.flags
            )

        if self.services is None:
            services = "None"
        else:
            services = "\n".join(
                f"| [`{service.name}`](<{service.path.as_posix()}>) | {service.port} | {service.type} |"
                for service in self.services
            )

        return CHALL_README_TEMPLATE.format(
            name=self.name,
            description=self.description,
            author=self.author,
            category=self.category,
            difficulty=self.difficulty,
            extras=extras,
            hints=hints,
            files=files,
            flags=flags,
            services=services,
        )


class ChallengeFile(Model):
    """Represents a chall.toml config file.

    Attributes:
        version (str): The specification version.
        challenge (Challenge): The challenge object.
    """

    version: str
    challenge: Challenge

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_challenge_version(value):
            raise ValueError(
                f'Unsupported specification version: "{value}", current version "{CHALLENGE_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_challenge(cls, challenge: Challenge) -> ChallengeFile:
        """Create a ChallengeFile object from a Challenge object.

        Args:
            challenge (Challenge): The Challenge object to convert.

        Returns:
            ChallengeFile: The converted ChallengeFile object.
        """
        return cls(version=str(CHALLENGE_SPEC_VERSION), challenge=challenge)
