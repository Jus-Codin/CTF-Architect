from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from pydantic import Field

from ctfa.core.workflow.actions import WorkflowAction
from ctfa.core.workflow.outputs import WorkflowOutput
from ctfa.models._base import Model
from ctfa.models.challenge import ChallengeConfig
from ctfa.models.workflow import WorkflowConfig, WorkflowKindConfig


class WorkflowKindValidationError(ValueError):
    """Raised when a workflow kind config payload is invalid."""


class WorkflowPlanContext(Model):
    """Shared context passed to each workflow-kind planner."""

    repository_path: Path
    workflow: WorkflowConfig
    selected_challenges: list[ChallengeConfig] = Field(default_factory=list)
    prior_step_actions: dict[str, list[WorkflowAction]] = Field(default_factory=dict)
    prior_step_outputs: dict[str, list[WorkflowOutput]] = Field(default_factory=dict)


class WorkflowKindPlanResult(Model):
    """Dry-run result returned by a workflow kind."""

    actions: list[WorkflowAction] = Field(default_factory=list)
    outputs: list[WorkflowOutput] = Field(default_factory=list)
    message: str | None = None


_ConfigModelT = TypeVar("_ConfigModelT", bound=WorkflowKindConfig)


class WorkflowKind(ABC):
    """Base class for all workflow kinds."""

    kind_name: str
    config_model: type[WorkflowKindConfig] = WorkflowKindConfig

    @classmethod
    def validate_config(cls, config: dict) -> WorkflowKindConfig:
        try:
            return cls.config_model.model_validate(config)
        except Exception as error:  # pragma: no cover - pydantic shapes exact exception type
            raise WorkflowKindValidationError(f'Invalid config for workflow kind "{cls.kind_name}": {error}') from error

    @abstractmethod
    def plan_step(self, context: WorkflowPlanContext, config: WorkflowKindConfig) -> WorkflowKindPlanResult:
        """Build deterministic dry-run actions and typed outputs for this workflow kind."""


_WORKFLOW_KIND_REGISTRY: dict[str, type[WorkflowKind]] = {}


def register_workflow_kind(kind_cls: type[WorkflowKind]) -> type[WorkflowKind]:
    """Register a workflow kind implementation by ``kind_name``."""
    kind_name = getattr(kind_cls, "kind_name", "").strip()
    if not kind_name:
        raise ValueError("Workflow kind classes must define a non-empty kind_name")

    if kind_name in _WORKFLOW_KIND_REGISTRY:
        raise ValueError(f'Workflow kind "{kind_name}" already registered')

    _WORKFLOW_KIND_REGISTRY[kind_name] = kind_cls
    return kind_cls


def get_workflow_kind(kind_name: str) -> type[WorkflowKind] | None:
    """Look up a registered workflow kind implementation."""
    return _WORKFLOW_KIND_REGISTRY.get(kind_name)
