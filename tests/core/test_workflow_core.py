from pathlib import Path

import pytest

from ctfa.constants import WORKFLOWS_CONFIG_FILE
from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.actions import CreateFileAction, UpdateFileAction, WorkflowActionResult
from ctfa.core.workflow.plan import WorkflowPlanner, WorkflowPlanningError
from ctfa.models.challenge import ChallengeConfig, ChallengeService
from ctfa.models.ctf_config import CTFConfig
from ctfa.models.workflow import WorkflowConfig


def test_workflow_planner_orders_dependencies_deterministically():
    workflows = [
        WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
        WorkflowConfig(name="lint", kind="validate"),
        WorkflowConfig(name="ports", kind="port-mapping"),
    ]

    ordered = WorkflowPlanner.plan_order(workflows)
    assert [workflow.name for workflow in ordered] == ["lint", "ports", "compose"]


def test_workflow_planner_missing_dependency_error():
    workflows = [WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"])]

    with pytest.raises(WorkflowPlanningError, match='depends on unknown workflow "ports"'):
        WorkflowPlanner.plan_order(workflows)


def test_workflow_planner_cycle_detection_error():
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping", depends_on=["compose"]),
        WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
    ]

    with pytest.raises(WorkflowPlanningError, match="Workflow dependency cycle detected"):
        WorkflowPlanner.plan_order(workflows)


def test_workflow_planner_dump_and_load_roundtrip(tmp_path: Path):
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping"),
        WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
    ]

    WorkflowPlanner.dump_config_file(tmp_path, workflows)
    loaded = WorkflowPlanner.load_config_file(tmp_path)

    assert [workflow.name for workflow in loaded] == ["ports", "compose"]
    assert (tmp_path / WORKFLOWS_CONFIG_FILE).is_file()


def test_workflow_actions_update_marks_change_status():
    update_action = UpdateFileAction(
        name="update compose",
        target_path=Path("compose.yaml"),
        old_content="a",
        new_content="b",
    )
    assert update_action.would_change is True

    no_change_action = UpdateFileAction(
        name="update compose",
        target_path=Path("compose.yaml"),
        old_content="a",
        new_content="a",
    )
    assert no_change_action.would_change is False


def test_workflow_action_result_tracks_changes():
    action = CreateFileAction(name="create mapping", target_path=Path("port_mapping.yaml"), content="ports: []")
    result = WorkflowActionResult(status="planned", message="dry-run", changes=[action])

    assert result.status == "planned"
    assert result.message == "dry-run"
    assert len(result.changes) == 1


def test_workflow_build_plan_deterministic_selected_challenge_order(tmp_path: Path):
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(
            name="Plan Repo",
            categories=["crypto", "web"],
            difficulties=["easy", "hard"],
        ),
    )

    challenge_a = Challenge.package(
        ChallengeConfig(
            id="web-b",
            name="Web B",
            description="B",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="b-folder",
        ),
        source_path,
    )
    challenge_b = Challenge.package(
        ChallengeConfig(
            id="web-a",
            name="Web A",
            description="A",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="a-folder",
        ),
        source_path,
    )

    repo.add_challenge(challenge_a, preserve_original=True)
    repo.add_challenge(challenge_b, preserve_original=True)

    WorkflowPlanner.dump_config_file(
        repo_path,
        [WorkflowConfig(name="compose", kind="docker-compose")],
    )

    plan = WorkflowPlanner.build_plan(repo_path)
    selected_ids = [challenge.id for challenge in plan.steps[0].selected_challenges]
    assert selected_ids == ["web-a", "web-b"]


def test_workflow_build_plan_generates_port_mapping_and_compose_actions(tmp_path: Path):
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(
            name="Plan Repo",
            categories=["web"],
            difficulties=["easy"],
            starting_port=41000,
        ),
    )

    challenge = Challenge.package(
        ChallengeConfig(
            id="web-a",
            name="Web A",
            description="A",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="a-folder",
            services=[
                ChallengeService(
                    type="web",
                    name="frontend",
                    path=source_path,
                    ports=[8080],
                )
            ],
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

    plan = WorkflowPlanner.build_plan(repo_path)

    assert len(plan.steps[0].actions) == 1
    assert plan.steps[0].actions[0].target_path.as_posix() == "port_mapping.yaml"
    assert len(plan.steps[1].actions) == 1
    assert plan.steps[1].actions[0].target_path.as_posix() == "compose.yml"


def test_workflow_build_plan_compose_uses_existing_port_mapping_file(tmp_path: Path):
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(
            name="Plan Repo",
            categories=["web"],
            difficulties=["easy"],
        ),
    )

    challenge = Challenge.package(
        ChallengeConfig(
            id="web-a",
            name="Web A",
            description="A",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="a-folder",
            services=[
                ChallengeService(
                    type="web",
                    name="frontend",
                    path=source_path,
                    ports=[8080],
                )
            ],
        ),
        source_path,
    )
    repo.add_challenge(challenge, preserve_original=True)

    (repo_path / "port_mapping.yaml").write_text(
        """
version: 0.1
mapping:
  web-web-a-frontend:
    - from_port: 8080
      to_port: 41000
""".strip()
        + "\n",
        encoding="utf-8",
    )

    WorkflowPlanner.dump_config_file(
        repo_path,
        [WorkflowConfig(name="compose", kind="docker-compose")],
    )

    plan = WorkflowPlanner.build_plan(repo_path)

    assert len(plan.steps) == 1
    assert plan.steps[0].workflow.name == "compose"
    assert len(plan.steps[0].actions) == 1
    assert plan.steps[0].actions[0].target_path.as_posix() == "compose.yml"


def test_workflow_build_plan_rejects_invalid_kind_config(tmp_path: Path):
    repo_path = tmp_path / "repo"
    ChallengeRepository.create(
        repo_path,
        CTFConfig(name="Repo", categories=["web"], difficulties=["easy"], starting_port=40000),
    )

    WorkflowPlanner.dump_config_file(
        repo_path,
        [
            WorkflowConfig(
                name="ports",
                kind="port-mapping",
                config={"filename": "x.yaml", "unknown": True},
            )
        ],
    )

    with pytest.raises(WorkflowPlanningError, match="Invalid config for workflow kind"):
        WorkflowPlanner.build_plan(repo_path)


def test_workflow_build_plan_include_exclude_filters(tmp_path: Path):
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(
            name="Filter Repo",
            categories=["crypto", "web"],
            difficulties=["easy", "hard"],
        ),
    )

    challenge = Challenge.package(
        ChallengeConfig(
            id="web-a",
            name="Web A",
            description="A",
            category="web",
            difficulty="easy",
            author="tester",
            folder_name="a-folder",
        ),
        source_path,
    )
    repo.add_challenge(challenge, preserve_original=True)

    WorkflowPlanner.dump_config_file(
        repo_path,
        [
            WorkflowConfig(name="ports", kind="port-mapping"),
            WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
            WorkflowConfig(name="ports-alt", kind="port-mapping", config={"filename": "port_mapping_alt.yaml"}),
        ],
    )

    included = WorkflowPlanner.build_plan(repo_path, include_workflows=["ports-alt"])
    assert [step.workflow.name for step in included.steps] == ["ports-alt"]

    excluded = WorkflowPlanner.build_plan(repo_path, exclude_workflows=["ports-alt"])
    assert [step.workflow.name for step in excluded.steps] == ["ports", "compose"]


def test_workflow_build_plan_filter_rejects_unknown_names(tmp_path: Path):
    repo_path = tmp_path / "repo"
    ChallengeRepository.create(
        repo_path,
        CTFConfig(
            name="Filter Repo",
            categories=["crypto"],
            difficulties=["easy"],
        ),
    )

    WorkflowPlanner.dump_config_file(
        repo_path,
        [WorkflowConfig(name="ports", kind="port-mapping")],
    )

    with pytest.raises(WorkflowPlanningError, match=r"Unknown workflow name\(s\) in include filter"):
        WorkflowPlanner.build_plan(repo_path, include_workflows=["missing"])

    with pytest.raises(WorkflowPlanningError, match=r"Unknown workflow name\(s\) in exclude filter"):
        WorkflowPlanner.build_plan(repo_path, exclude_workflows=["missing"])
