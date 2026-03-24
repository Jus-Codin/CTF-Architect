from __future__ import annotations

from pathlib import Path

from ctfa.core.workflow.actions import WorkflowActionResult
from ctfa.core.workflow.actions import WorkflowApplyError as WorkflowApplyError
from ctfa.core.workflow.actions import WorkflowConflictError as WorkflowConflictError
from ctfa.core.workflow.plan import WorkflowPlan, WorkflowPlanStep


def apply_workflow_plan(
    repository_path: str | Path,
    plan: WorkflowPlan,
    *,
    dry_run: bool = False,
    fail_on_conflict: bool = True,
) -> WorkflowPlan:
    """Apply planned workflow actions safely to disk."""
    repo_path = Path(repository_path)
    steps: list[WorkflowPlanStep] = []

    for step in plan.steps:
        if not step.actions:
            steps.append(
                WorkflowPlanStep(
                    workflow=step.workflow,
                    selected_challenges=step.selected_challenges,
                    actions=step.actions,
                    outputs=step.outputs,
                    result=WorkflowActionResult(
                        status="unchanged",
                        message=step.result.message or "No changes needed",
                        changes=[],
                    ),
                )
            )
            continue

        action_messages: list[str] = []
        try:
            for action in step.actions:
                action_message = action.apply(repo_path, dry_run=dry_run, fail_on_conflict=fail_on_conflict)
                if action_message:
                    action_messages.append(action_message)
            status = "planned" if dry_run else "success"
            if action_messages:
                message = "; ".join(action_messages)
            else:
                message = "Dry-run apply completed" if dry_run else "Applied successfully"
        except WorkflowApplyError as error:
            if fail_on_conflict:
                raise
            status = "failure"
            message = str(error)

        steps.append(
            WorkflowPlanStep(
                workflow=step.workflow,
                selected_challenges=step.selected_challenges,
                actions=step.actions,
                outputs=step.outputs,
                result=WorkflowActionResult(status=status, message=message, changes=step.actions),
            )
        )

    return WorkflowPlan(steps=steps)
