from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ruamel.yaml.comments import CommentedMap

from ctfa.constants import WORKFLOWS_CONFIG_FILE, WORKFLOWS_CONFIG_HEADER

# Ensure built-in workflow kinds are registered.
from ctfa.core import workflows as _builtin_workflows  # noqa: F401
from ctfa.core.exceptions import ConfigFileNotFoundError
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.actions import WorkflowAction, WorkflowActionResult
from ctfa.core.workflow.base import (
    WorkflowKindPlanResult,
    WorkflowKindValidationError,
    WorkflowPlanContext,
    get_workflow_kind,
)
from ctfa.core.workflow.outputs import WorkflowOutput
from ctfa.core.workflow.selectors import filter_challenges
from ctfa.models._base import Model
from ctfa.models.challenge import ChallengeConfig
from ctfa.models.workflow import WorkflowConfig, WorkflowsConfigFile
from ctfa.utils import yaml


class WorkflowPlanningError(ValueError):
    """Raised when workflow planning fails due to invalid dependencies or cycles."""


class WorkflowPlanStep(Model):
    """Represents one planned workflow execution step."""

    workflow: WorkflowConfig
    selected_challenges: list[ChallengeConfig]
    actions: list[WorkflowAction]
    outputs: list[WorkflowOutput]
    result: WorkflowActionResult


class WorkflowPlan(Model):
    """Represents the full dry-run workflow plan."""

    steps: list[WorkflowPlanStep]


class WorkflowPlanner:
    @staticmethod
    def _select_workflows(
        workflows: list[WorkflowConfig],
        include_workflows: list[str] | None = None,
        exclude_workflows: list[str] | None = None,
    ) -> list[WorkflowConfig]:
        available = {workflow.name for workflow in workflows}
        include = set(include_workflows or [])
        exclude = set(exclude_workflows or [])

        unknown_include = sorted(name for name in include if name not in available)
        if unknown_include:
            raise WorkflowPlanningError(f"Unknown workflow name(s) in include filter: {', '.join(unknown_include)}")

        unknown_exclude = sorted(name for name in exclude if name not in available)
        if unknown_exclude:
            raise WorkflowPlanningError(f"Unknown workflow name(s) in exclude filter: {', '.join(unknown_exclude)}")

        selected = workflows
        if include:
            selected = [workflow for workflow in selected if workflow.name in include]

        if exclude:
            selected = [workflow for workflow in selected if workflow.name not in exclude]

        if not selected:
            raise WorkflowPlanningError("No workflows remain after include/exclude filters.")

        return selected

    @staticmethod
    def _resolve_config_file(path: str | Path) -> Path:
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            return path

        config_path = path / WORKFLOWS_CONFIG_FILE
        if not config_path.is_file():
            raise ConfigFileNotFoundError(path, "workflows config")

        return config_path

    @staticmethod
    def load_config_file(path: str | Path) -> list[WorkflowConfig]:
        config_path = WorkflowPlanner._resolve_config_file(path)

        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.load(handle)

        config_file = WorkflowsConfigFile.model_validate(data)
        return config_file.workflows

    @staticmethod
    def dump_config_file(path: str | Path, workflows: list[WorkflowConfig]) -> None:
        if isinstance(path, str):
            path = Path(path)

        if path.is_file():
            config_path = path
        else:
            config_path = path / WORKFLOWS_CONFIG_FILE

        if config_path.exists() and config_path.is_file():
            with config_path.open("r", encoding="utf-8") as handle:
                document = yaml.load(handle) or CommentedMap()
                if not isinstance(document, CommentedMap):
                    document = CommentedMap(document)
        else:
            document = CommentedMap()

        config_file = WorkflowsConfigFile.from_workflows(workflows)
        payload = config_file.model_dump(mode="json", exclude_defaults=True, exclude_none=True)
        document["version"] = payload["version"]
        document["workflows"] = payload["workflows"]
        document.yaml_set_start_comment(WORKFLOWS_CONFIG_HEADER + "\n")
        document.yaml_set_comment_before_after_key("workflows", before="\n")

        with config_path.open("w", encoding="utf-8") as handle:
            yaml.dump(document, handle)

    @staticmethod
    def plan_order(workflows: list[WorkflowConfig]) -> list[WorkflowConfig]:
        by_name: dict[str, WorkflowConfig] = {}
        for workflow in workflows:
            if workflow.name in by_name:
                raise WorkflowPlanningError(f'Duplicate workflow name "{workflow.name}" detected.')
            by_name[workflow.name] = workflow

        in_degree: dict[str, int] = {name: 0 for name in by_name}
        graph: dict[str, set[str]] = defaultdict(set)

        for workflow in workflows:
            for dependency in workflow.depends_on:
                if dependency not in by_name:
                    raise WorkflowPlanningError(
                        f'Workflow "{workflow.name}" depends on unknown workflow "{dependency}".'
                    )
                if workflow.name not in graph[dependency]:
                    graph[dependency].add(workflow.name)
                    in_degree[workflow.name] += 1

        ready = sorted(name for name, degree in in_degree.items() if degree == 0)
        ordered_names: list[str] = []

        while ready:
            name = ready.pop(0)
            ordered_names.append(name)

            for dependent_name in sorted(graph[name]):
                in_degree[dependent_name] -= 1
                if in_degree[dependent_name] == 0:
                    ready.append(dependent_name)
                    ready.sort()

        if len(ordered_names) != len(by_name):
            unresolved = {name for name, degree in in_degree.items() if degree > 0}
            cycle = WorkflowPlanner._find_cycle(unresolved, workflows)
            if cycle:
                cycle_path = " -> ".join(cycle)
                raise WorkflowPlanningError(f"Workflow dependency cycle detected: {cycle_path}")
            raise WorkflowPlanningError("Workflow dependency cycle detected.")

        return [by_name[name] for name in ordered_names]

    @staticmethod
    def _find_cycle(unresolved: set[str], workflows: list[WorkflowConfig]) -> list[str] | None:
        dependencies = {
            workflow.name: [dependency for dependency in workflow.depends_on if dependency in unresolved]
            for workflow in workflows
            if workflow.name in unresolved
        }
        visited: set[str] = set()
        stack: list[str] = []
        in_stack: set[str] = set()

        def _dfs(node: str) -> list[str] | None:
            visited.add(node)
            stack.append(node)
            in_stack.add(node)

            for dependency in sorted(dependencies.get(node, [])):
                if dependency not in visited:
                    cycle = _dfs(dependency)
                    if cycle is not None:
                        return cycle
                elif dependency in in_stack:
                    start = stack.index(dependency)
                    return stack[start:] + [dependency]

            stack.pop()
            in_stack.remove(node)
            return None

        for name in sorted(unresolved):
            if name in visited:
                continue
            cycle = _dfs(name)
            if cycle is not None:
                return cycle

        return None

    @staticmethod
    def build_plan(
        repository_path: str | Path,
        workflows_path: str | Path | None = None,
        *,
        include_workflows: list[str] | None = None,
        exclude_workflows: list[str] | None = None,
    ) -> WorkflowPlan:
        repo = ChallengeRepository.load_repository(repository_path)

        workflows = WorkflowPlanner.load_config_file(workflows_path or repo.location)
        selected_workflows = WorkflowPlanner._select_workflows(
            workflows,
            include_workflows=include_workflows,
            exclude_workflows=exclude_workflows,
        )
        ordered_workflows = WorkflowPlanner.plan_order(selected_workflows)

        challenges = [
            challenge.config
            for challenge in repo.walk_challenges(
                skip_invalid=True,
                ignore_errors=True,
            )
        ]

        steps: list[WorkflowPlanStep] = []
        prior_step_actions: dict[str, list[WorkflowAction]] = {}
        prior_step_outputs: dict[str, list[WorkflowOutput]] = {}
        for workflow in ordered_workflows:
            selected = filter_challenges(challenges, workflow.selectors)
            selected = sorted(selected, key=lambda challenge: (challenge.category, challenge.folder_name, challenge.id))

            workflow_kind_class = get_workflow_kind(workflow.kind)
            if workflow_kind_class is None:
                raise WorkflowPlanningError(f'Unknown workflow kind "{workflow.kind}" for workflow "{workflow.name}".')

            try:
                config = workflow_kind_class.validate_config(workflow.config)
            except WorkflowKindValidationError as error:
                raise WorkflowPlanningError(str(error)) from error

            context = WorkflowPlanContext(
                repository_path=repo.location,
                workflow=workflow,
                selected_challenges=selected,
                prior_step_actions={key: value[:] for key, value in prior_step_actions.items()},
                prior_step_outputs={key: value[:] for key, value in prior_step_outputs.items()},
            )

            try:
                step_plan = workflow_kind_class().plan_step(context, config)
            except ValueError as error:
                raise WorkflowPlanningError(
                    f'Workflow "{workflow.name}" ({workflow.kind}) planning failed: {error}'
                ) from error
            if not isinstance(step_plan, WorkflowKindPlanResult):
                raise WorkflowPlanningError(
                    f'Workflow "{workflow.name}" ({workflow.kind}) returned an invalid plan result.'
                )

            if step_plan.actions:
                result = WorkflowActionResult(
                    status="planned",
                    message=step_plan.message,
                    changes=step_plan.actions,
                )
            else:
                result = WorkflowActionResult(
                    status="unchanged",
                    message=step_plan.message or "No changes needed",
                    changes=[],
                )
            prior_step_actions[workflow.name] = step_plan.actions
            prior_step_outputs[workflow.name] = step_plan.outputs

            steps.append(
                WorkflowPlanStep(
                    workflow=workflow,
                    selected_challenges=selected,
                    actions=step_plan.actions,
                    outputs=step_plan.outputs,
                    result=result,
                )
            )

        return WorkflowPlan(steps=steps)
