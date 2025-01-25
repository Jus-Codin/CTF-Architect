from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator

from ctf_architect.models.base import Model
from ctf_architect.version import (
    CTF_CONFIG_SPEC_VERSION,
    is_supported_ctf_config_version,
)


class ExtraField(Model):
    """Represents an extra field for a challenge.

    Attributes:
        name (str): The name of the extra field.
        description (str): The description of the extra field.
        prompt (str): The prompt of the extra field.
        required (bool): Specifies whether the extra field is required.
        type (Literal["string", "integer", "float", "boolean"]): The type of the extra field.
    """

    name: str
    description: str
    prompt: str
    required: bool
    type: Literal["string", "integer", "float", "boolean"]


class CTFConfig(Model):
    """Represents the configuration for a CTF.

    Attributes:
        categories (list[str]): The list of categories for the CTF.
        difficulties (list[str]): The list of difficulties for the CTF.
        flag_format (str | None): The flag format for the CTF.
        starting_port (int | None): The starting port for services in the CTF.
        name (str): The name of the CTF.
        extras (list[ExtraField] | None): The list of extra fields for challenges in the CTF.
    """

    categories: list[str]
    difficulties: list[str]
    flag_format: str | None = None
    starting_port: int | None = None
    name: str
    extras: Annotated[list[ExtraField], Field(min_length=1)] | None = None


class ConfigFile(Model):
    """Represents a ctf_config.toml config file.

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
                f'Unsupported specification version: "{value}", current version "{CTF_CONFIG_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_ctf_config(cls, config: CTFConfig) -> ConfigFile:
        """Create a ConfigFile object from a CTFConfig object.

        Args:
            config (CTFConfig): The CTFConfig object to convert.

        Returns:
            ConfigFile: The converted ConfigFile object.
        """
        return cls(version=str(CTF_CONFIG_SPEC_VERSION), config=config)
