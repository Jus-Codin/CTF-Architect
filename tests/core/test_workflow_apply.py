from pathlib import Path

import pytest

from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.actions import WorkflowAction
from ctfa.core.workflow.apply import WorkflowConflictError, apply_workflow_plan
from ctfa.core.workflow.plan import WorkflowPlanner
from ctfa.models.challenge import ChallengeConfig, ChallengeService
from ctfa.models.ctf_config import CTFConfig
from ctfa.models.workflow import WorkflowConfig


def _build_repo_with_service(tmp_path: Path) -> Path:
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(name="Apply Repo", categories=["web"], difficulties=["easy"], starting_port=43000),
    )

    challenge = Challenge.package(
        ChallengeConfig(
            id="web-a",
            name="Web A",
            description="A",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="web-a",
            services=[ChallengeService(type="web", name="frontend", path=source_path, ports=[8080])],
        ),
        source_path,
    )
    repo.add_challenge(challenge, preserve_original=True)

    WorkflowPlanner.dump_config_file(
        repo_path,
        [
            WorkflowConfig(name="ports", kind="port-mapping"),
            WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
        ],
    )

    return repo_path


def test_apply_workflow_plan_writes_planned_files(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    plan = WorkflowPlanner.build_plan(repo_path)

    result = apply_workflow_plan(repo_path, plan)

    assert (repo_path / "port_mapping.yaml").is_file()
    assert (repo_path / "compose.yml").is_file()
    assert all(step.result.status == "success" for step in result.steps)


def test_apply_workflow_plan_dry_run_does_not_write_files(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    plan = WorkflowPlanner.build_plan(repo_path)

    result = apply_workflow_plan(repo_path, plan, dry_run=True)

    assert not (repo_path / "port_mapping.yaml").exists()
    assert not (repo_path / "compose.yml").exists()
    assert all(step.result.status == "planned" for step in result.steps)


def test_apply_workflow_plan_conflict_raises(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    plan = WorkflowPlanner.build_plan(repo_path)
    (repo_path / "port_mapping.yaml").write_text("existing", encoding="utf-8")

    with pytest.raises(WorkflowConflictError, match="Create conflict"):
        apply_workflow_plan(repo_path, plan, fail_on_conflict=True)


class WriteMarkerAction(WorkflowAction):
    kind: str = "http"
    action: str = "write-marker"
    marker: str

    def apply(self, repository_path: Path, *, dry_run: bool, fail_on_conflict: bool) -> str | None:
        if not dry_run:
            self.metadata["response"] = f"sent:{self.marker}"
        return "marker sent"


def test_apply_workflow_plan_supports_custom_actions(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    plan = WorkflowPlanner.build_plan(repo_path, include_workflows=["ports"])

    plan.steps[0].actions = [
        WriteMarkerAction(
            name="custom-marker",
            marker="ok",
        )
    ]

    result = apply_workflow_plan(repo_path, plan)

    assert plan.steps[0].actions[0].metadata["response"] == "sent:ok"
    assert result.steps[0].result.status == "success"
    assert result.steps[0].result.message == "marker sent"
