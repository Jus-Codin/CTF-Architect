from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ctf_architect.models.base import Model, SlugStr
from ctf_architect.version import DEPLOYMENTS_SPEC_VERSION, is_supported_deployments_config_version


# Needs to be a BaseModel as it needs to be frozen
class SelectorRule(BaseModel):
    """Selector rules to apply to a challenge field.

    If multiple matchers are specified, it is equivalent to an AND condition.
    If multiple values are specified for a matcher, it is equivalent to an OR condition, unless one of the matchers is `key` or `exists`.

    Attributes:
        value (str | list[str], optional): The exact value to match.
        length (int | list[int], optional): The length of the iterable to match.
        contains (str | list[str], optional): The substring(s) or item(s) to match within the value.
        pattern (str | list[str], optional): The regex pattern(s) to match against the value.
        expression (str | list[str], optional): The expression to evaluate the value with.
        key (str | list[str], optional): A special matcher to match to keys inside an object or dictionary. If multiple keys are given, any of the keys can match.
                                         The key can also be a dot-separated path to match nested keys.
        exists (bool, optional): Whether the given field or key(s) in the field must exist.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    # Generic matchers
    value: str | list[str] | None = None

    # Iterable matchers
    length: int | list[int] | None = None
    contains: str | list[str] | None = None

    # String matchers
    pattern: str | list[str] | None = None

    # Integer matchers
    expression: str | list[str] | None = None

    # Object / Dict matchers
    key: str | list[str] | None = None
    exists: bool | None = None


class Selectors(Model):
    """Selectors for filtering challenges for a given deployment.

    If multiple rules are specified, any service that fulfils any of the rules will be selected.
    Setting `include` to `"*"` will include all challenges, while setting `exclude` to `"*"` will exclude all challenges (which is actually the default behavior).

    Exclusion rules are applied after inclusion rules. As such, if `exclude` is set to `"*"`, no challenge will be included.

    Attributes:
        include (Literal["*"] | list[dict[str, SelectorRule]], optional): A list of field names to selector rules to include for the selector.
        exclude (Literal["*"] | list[dict[str, SelectorRule]], optional): A list of field names to selector rules to exclude for the selector.
    """

    include: Literal["*"] | list[dict[str, SelectorRule]] | None = None
    exclude: Literal["*"] | list[dict[str, SelectorRule]] | None = None


class DeploymentConfig(Model):
    """Represents a single deployment configuration.

    Attributes:
        name (SlugStr): The name of the deployment.
        strategy (SlugStr): The deployment strategy to use.
        config (dict[str, Any], optional): The configuration options for the deployment.
        selectors (Selector): The selectors to use for the deployment.
        output_dir (Path, optional): The output directory for the deployment artifacts.
        depends_on (list[SlugStr], optional): A list of names of other deployments that this deployment depends on.
    """

    name: SlugStr
    strategy: SlugStr
    config: dict[str, Any] = Field(default_factory=dict)
    selectors: Selectors | None = None
    output_dir: Path | None = None
    depends_on: list[SlugStr] = Field(default_factory=list)

    @field_validator("output_dir", mode="after")
    def _validate_output_dir(cls, value: Path | None) -> Path | None:
        if value is not None and value.is_absolute():
            raise ValueError("Output directory must be a relative path.")
        return value


class DeploymentsConfigFile(Model):
    """Represents a ctf_deploy.yaml file.

    Attributes:
        version (str): The version of the deployment configuration.
        deployments (list[DeploymentConfig]): The list of deployment configurations.
    """

    version: str
    deployments: list[DeploymentConfig] = Field(default_factory=list)

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_deployments_config_version(value):
            raise ValueError(
                f'Unsupported Deployments specification version: "{value}", current version "{DEPLOYMENTS_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_deployments(cls, deployments: list[DeploymentConfig]) -> DeploymentsConfigFile:
        """Create a DeploymentsConfigFile from a list of DeploymentConfig objects.

        Args:
            deployments (list[DeploymentConfig]): The list of deployment configurations.

        Returns:
            DeploymentsConfigFile: The created DeploymentsConfigFile instance.
        """
        return cls(version=str(DEPLOYMENTS_SPEC_VERSION), deployments=deployments)
