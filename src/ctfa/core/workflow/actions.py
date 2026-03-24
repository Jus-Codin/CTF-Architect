from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_serializer, model_validator

from ctfa.models._base import Model


class WorkflowApplyError(ValueError):
    """Raised when workflow apply fails."""


class WorkflowConflictError(WorkflowApplyError):
    """Raised when an apply conflict is detected."""


class WorkflowAction(Model, ABC):
    """Base action model produced by workflow planning."""

    name: str
    description: str | None = None
    kind: str = "custom"
    action: str
    dry_run: bool = True
    would_change: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def apply(self, repository_path: Path, *, dry_run: bool, fail_on_conflict: bool) -> str | None:
        """Apply this action and optionally return a success/info message."""


class FileWorkflowAction(WorkflowAction, ABC):
    """Base class for file-system workflow actions."""

    kind: Literal["file"] = "file"  # type: ignore
    target_path: Path

    @staticmethod
    def _write_content(target_path: Path, content: str | bytes | None) -> None:
        if isinstance(content, bytes):
            target_path.write_bytes(content)
            return

        target_path.write_text(content or "", encoding="utf-8")

    @field_serializer("target_path")
    def _serialize_target_path(self, value: Path) -> str:
        return value.as_posix()

    def resolve_target_path(self, repository_path: Path) -> Path:
        """Resolve and validate this action's target path under repository root."""
        target = self.target_path if self.target_path.is_absolute() else (repository_path / self.target_path)
        resolved_target = target.resolve()
        resolved_repo = repository_path.resolve()

        if resolved_target != resolved_repo and resolved_repo not in resolved_target.parents:
            raise WorkflowApplyError(f"Refusing to write outside repository root: {self.target_path}")

        return resolved_target


class CreateFileAction(FileWorkflowAction):
    """Represents creating a new file."""

    action: Literal["create"] = "create"  # type: ignore
    content: str | bytes | None = None

    def apply(self, repository_path: Path, *, dry_run: bool, fail_on_conflict: bool) -> str | None:
        target_path = self.resolve_target_path(repository_path)

        if target_path.exists():
            message = f"Create conflict: target already exists: {self.target_path.as_posix()}"
            if fail_on_conflict:
                raise WorkflowConflictError(message)
            return message

        if dry_run:
            return f"Would create {self.target_path.as_posix()}"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_content(target_path, self.content)
        return f"Created {self.target_path.as_posix()}"


class UpdateFileAction(FileWorkflowAction):
    """Represents updating an existing file."""

    action: Literal["update"] = "update"  # type: ignore
    old_content: str | bytes | None = None
    new_content: str | bytes | None = None

    @model_validator(mode="after")
    def _compute_would_change(self) -> UpdateFileAction:
        object.__setattr__(self, "would_change", self.old_content != self.new_content)
        return self

    def apply(self, repository_path: Path, *, dry_run: bool, fail_on_conflict: bool) -> str | None:
        target_path = self.resolve_target_path(repository_path)

        if not target_path.exists():
            message = f"Update conflict: target does not exist: {self.target_path.as_posix()}"
            if fail_on_conflict:
                raise WorkflowConflictError(message)
            return message

        current = (
            target_path.read_bytes() if isinstance(self.old_content, bytes) else target_path.read_text(encoding="utf-8")
        )
        if self.old_content is not None and current != self.old_content:
            message = f"Update conflict: existing content changed since planning: {self.target_path.as_posix()}"
            if fail_on_conflict:
                raise WorkflowConflictError(message)
            return message

        if dry_run:
            return f"Would update {self.target_path.as_posix()}"

        if self.new_content is None:
            return f"No new content provided for {self.target_path.as_posix()}"

        self._write_content(target_path, self.new_content)
        return f"Updated {self.target_path.as_posix()}"


class WorkflowActionResult(Model):
    """Outcome from executing or planning one or more workflow actions."""

    status: Literal["planned", "success", "failure", "skipped", "unchanged"]
    message: str | None = None
    changes: list[WorkflowAction] = Field(default_factory=list)
