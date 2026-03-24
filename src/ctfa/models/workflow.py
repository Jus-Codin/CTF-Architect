from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ctfa.models._base import Model, SlugStr
from ctfa.version import WORKFLOWS_SPEC_VERSION, is_supported_workflows_config_version


class SelectorRule(BaseModel):
    """Selector matchers for a specific field.

    Matchers within a rule are ANDed together.
    List values for a matcher are ORed together.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    value: str | int | float | bool | list[str | int | float | bool] | None = None
    length: int | list[int] | None = None
    contains: str | int | float | bool | list[str | int | float | bool] | None = None
    pattern: str | list[str] | None = None
    key: str | list[str] | None = None
    exists: bool | None = None

    @field_validator("pattern")
    def _validate_pattern(cls, value: str | list[str] | None) -> str | list[str] | None:
        patterns = [value] if isinstance(value, str) else value
        if patterns is None:
            return value

        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                raise ValueError(f"Invalid regex pattern: {pattern}") from error

        return value


class Selectors(Model):
    """Selectors for filtering challenge inclusion in a workflow."""

    include: Literal["*"] | list[dict[str, SelectorRule]] | None = None
    exclude: Literal["*"] | list[dict[str, SelectorRule]] | None = None


class WorkflowConfig(Model):
    """Represents a single workflow configuration entry."""

    name: SlugStr
    kind: SlugStr
    config: dict[str, Any] = Field(default_factory=dict)
    selectors: Selectors | None = None
    output_dir: Path | None = None
    depends_on: list[SlugStr] = Field(default_factory=list)

    @field_validator("output_dir", mode="after")
    def _validate_output_dir(cls, value: Path | None) -> Path | None:
        if value is not None and (value.is_absolute() or value.as_posix().startswith("/")):
            raise ValueError("Output directory must be a relative path.")
        return value

    @field_serializer("output_dir")
    def _serialize_output_dir(self, value: Path | None) -> str | None:
        if value is None:
            return None
        return value.as_posix()


class WorkflowKindConfig(Model):
    """Base model for workflow-kind-specific ``WorkflowConfig.config`` payloads."""

    model_config = ConfigDict(extra="forbid")


class WorkflowsConfigFile(Model):
    """Represents a workflows config file."""

    version: str
    workflows: list[WorkflowConfig] = Field(default_factory=list)

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_workflows_config_version(value):
            raise ValueError(
                f'Unsupported Workflows specification version: "{value}", current version "{WORKFLOWS_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_workflows(cls, workflows: list[WorkflowConfig]) -> WorkflowsConfigFile:
        return cls(version=str(WORKFLOWS_SPEC_VERSION), workflows=workflows)
