from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ResolvedExistingFile

from ctfa.cli.param_types import ResolvedExistingChallengeRepository


def command(
    repository_path: Annotated[
        ResolvedExistingChallengeRepository, Parameter(name=["--repository", "-R"])
    ] = Path.cwd(),
    *,
    workflows_file: Annotated[ResolvedExistingFile | None, Parameter(name=["--workflows", "-w"])] = None,
    include_workflows: Annotated[
        list[str] | None,
        Parameter(name=["--workflow", "-W"], consume_multiple=True),
    ] = None,
    exclude_workflows: Annotated[
        list[str] | None,
        Parameter(name=["--exclude-workflow", "-X"], consume_multiple=True),
    ] = None,
    dry_run: Annotated[bool, Parameter(name=["--dry-run"])] = False,
    fail_on_conflict: Annotated[bool, Parameter(name=["--fail-on-conflict"])] = True,
):
    """Apply a workflow plan to repository files with conflict checks."""
    from ctfa.cli.ui.console import console
    from ctfa.core.exceptions import ConfigFileNotFoundError, InvalidChallengeRepositoryError
    from ctfa.core.workflow.apply import WorkflowApplyError, apply_workflow_plan
    from ctfa.core.workflow.plan import WorkflowPlanner, WorkflowPlanningError

    try:
        plan = WorkflowPlanner.build_plan(
            repository_path,
            workflows_file,
            include_workflows=include_workflows,
            exclude_workflows=exclude_workflows,
        )
        applied_plan = apply_workflow_plan(
            repository_path,
            plan,
            dry_run=dry_run,
            fail_on_conflict=fail_on_conflict,
        )
    except (InvalidChallengeRepositoryError, ConfigFileNotFoundError) as error:
        console.print(str(error), style="ctfa.error")
        raise SystemExit(1) from error
    except (WorkflowPlanningError, WorkflowApplyError) as error:
        console.print(str(error), style="ctfa.error")
        raise SystemExit(1) from error

    console.print("Workflow Apply", style="ctfa.title")
    for index, step in enumerate(applied_plan.steps, start=1):
        console.print(
            f"{index}. {step.workflow.name} ({step.workflow.kind})",
            style="ctfa.info",
        )
        console.print(f"   actions: {len(step.actions)}", style="ctfa.info")
        console.print(f"   status: {step.result.status}", style="ctfa.info")
        if step.result.message:
            console.print(f"   note: {step.result.message}", style="ctfa.info")
