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
):
    """Build and print a dry-run workflow plan for a repository.

    Args:
        repository_path (ResolvedExistingChallengeRepository, optional): Path to the challenge repository
        workflows_file (ResolvedExistingFile | None, optional): Optional explicit workflows config path
        include_workflows (list[str] | None, optional): Optional list of workflow names to include
        exclude_workflows (list[str] | None, optional): Optional list of workflow names to exclude
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.exceptions import ConfigFileNotFoundError, InvalidChallengeRepositoryError
    from ctfa.core.workflow.plan import WorkflowPlanner, WorkflowPlanningError

    try:
        plan = WorkflowPlanner.build_plan(
            repository_path,
            workflows_file,
            include_workflows=include_workflows,
            exclude_workflows=exclude_workflows,
        )
    except (InvalidChallengeRepositoryError, ConfigFileNotFoundError) as error:
        console.print(str(error), style="ctfa.error")
        raise SystemExit(1) from error
    except WorkflowPlanningError as error:
        console.print(str(error), style="ctfa.error")
        raise SystemExit(1) from error

    console.print("Workflow Plan", style="ctfa.title")
    for index, step in enumerate(plan.steps, start=1):
        depends_on = ", ".join(step.workflow.depends_on) if step.workflow.depends_on else "none"
        console.print(
            f"{index}. {step.workflow.name} ({step.workflow.kind})",
            style="ctfa.info",
        )
        console.print(f"   dependencies: {depends_on}", style="ctfa.info")
        console.print(f"   selected challenges: {len(step.selected_challenges)}", style="ctfa.info")

        if step.selected_challenges:
            for challenge in step.selected_challenges:
                console.print(
                    f"   - {challenge.category}/{challenge.folder_name} [{challenge.id}]",
                    style="ctfa.info",
                )

        if step.actions:
            console.print(f"   planned actions: {len(step.actions)}", style="ctfa.info")
            for action in step.actions:
                target = getattr(action, "target_path", None)
                target_display = target.as_posix() if isinstance(target, Path) else "(no file target)"
                console.print(
                    f"   - {action.action} {target_display} ({action.name})",
                    style="ctfa.info",
                )
        else:
            console.print("   planned actions: none", style="ctfa.warning")

        if step.result.message:
            console.print(f"   note: {step.result.message}", style="ctfa.warning")

        console.print()
