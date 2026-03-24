from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StringConstraints, field_validator

from ctfa.models._base import Model
from ctfa.version import CTF_CONFIG_SPEC_VERSION, is_supported_ctf_config_version

_LowerNonEmptyStr: TypeAlias = Annotated[str, StringConstraints(to_lower=True, min_length=1)]


class ExtraLabelConfig(Model):
    """Represents the configuration for an extra label for challenges.

    Attributes:
        name (str): The name of the extra label.
        description (str): The description of the extra label.
        prompt (str): The prompt of the extra label.
        type (Literal["string", "integer", "float", "boolean"]): The type of the extra label.
        required (bool): Specifies whether the extra label is required.
    """

    name: str
    description: str
    prompt: str
    type: Literal["string", "integer", "float", "boolean"]
    required: bool


class CTFConfig(Model):
    """Represents the configuration for a CTF.

    Attributes:
        name (str): The name of the CTF.
        categories (list[str]): The list of categories for the CTF.
        difficulties (list[str]): The list of difficulties for the CTF.
        flag_format (str, optional): The flag format for the CTF.
        starting_port (int, optional): The starting port for services in the CTF.
        extra_labels (list[ExtraLabelConfig], optional): The list of extra labels for challenges in the CTF.
    """

    name: str
    flag_format: str | None = None
    starting_port: int | None = None
    categories: Annotated[list[_LowerNonEmptyStr], Field(min_length=1)]
    difficulties: Annotated[list[_LowerNonEmptyStr], Field(min_length=1)]
    extra_labels: list[ExtraLabelConfig] | None = None


class RepositoryConfigFile(Model):
    """Represents a Repository config file.

    Attributes:
        version (str): The specification version.
        config (CTFConfig): The CTF config object.
    """

    version: str
    config: CTFConfig

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_ctf_config_version(value):
            raise ValueError(
                f'Unsupported CTF Config specification version: "{value}", current version "{CTF_CONFIG_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_ctf_config(cls, ctf_config: CTFConfig) -> RepositoryConfigFile:
        """Creates a RepositoryConfigFile from a CTFConfig.

        Args:
            ctf_config (CTFConfig): The CTF config object.

        Returns:
            RepositoryConfigFile: The created RepositoryConfigFile object.
        """
        return cls(version=str(CTF_CONFIG_SPEC_VERSION), config=ctf_config)
