from pathlib import Path

from ctfa.constants import WORKFLOWS_CONFIG_HEADER
from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.apply import apply_workflow_plan
from ctfa.core.workflow.outputs import ComposeWorkflowOutput, PortMappingWorkflowOutput
from ctfa.core.workflow.plan import WorkflowPlanner
from ctfa.models.challenge import ChallengeConfig, ChallengeService
from ctfa.models.ctf_config import CTFConfig
from ctfa.models.workflow import WorkflowConfig
from ctfa.utils import yaml


def _build_repo_with_service(tmp_path: Path) -> Path:
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(name="Workflow Repo", categories=["web"], difficulties=["easy"], starting_port=45000),
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
            services=[
                ChallengeService(
                    type="web",
                    name="frontend",
                    path=source_path,
                    ports=[8080],
                    annotations={
                        "privileged": True,
                        "ctfa.compose.extras": {
                            "labels": {"team": "blue"},
                            "build": "ignored",
                        },
                    },
                )
            ],
        ),
        source_path,
    )
    repo.add_challenge(challenge, preserve_original=True)

    return repo_path


def test_workflow_dump_config_file_writes_header(tmp_path: Path):
    WorkflowPlanner.dump_config_file(tmp_path, [WorkflowConfig(name="ports", kind="port-mapping")])

    content = (tmp_path / "ctf_workflows.yaml").read_text(encoding="utf-8")
    assert WORKFLOWS_CONFIG_HEADER.splitlines()[0] in content


def test_workflow_plan_exposes_typed_outputs_and_unchanged_steps(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    WorkflowPlanner.dump_config_file(
        repo_path,
        [
            WorkflowConfig(name="ports", kind="port-mapping"),
            WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
        ],
    )

    initial_plan = WorkflowPlanner.build_plan(repo_path)
    assert isinstance(initial_plan.steps[0].outputs[0], PortMappingWorkflowOutput)
    assert isinstance(initial_plan.steps[1].outputs[0], ComposeWorkflowOutput)

    apply_workflow_plan(repo_path, initial_plan)

    next_plan = WorkflowPlanner.build_plan(repo_path)
    assert all(step.result.status == "unchanged" for step in next_plan.steps)
    assert all(not step.actions for step in next_plan.steps)


def test_port_mapping_hash_strategy_and_compose_annotations(tmp_path: Path):
    repo_path = _build_repo_with_service(tmp_path)
    WorkflowPlanner.dump_config_file(
        repo_path,
        [
            WorkflowConfig(
                name="ports",
                kind="port-mapping",
                config={"strategy": "hash"},
            ),
            WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
        ],
    )

    plan = WorkflowPlanner.build_plan(repo_path)
    apply_workflow_plan(repo_path, plan)

    with (repo_path / "port_mapping.yaml").open("r", encoding="utf-8") as handle:
        mapping_payload = yaml.load(handle)

    with (repo_path / "compose.yml").open("r", encoding="utf-8") as handle:
        compose_payload = yaml.load(handle)

    service_mapping = mapping_payload["mapping"]["web-web-a-frontend"][0]
    assert service_mapping["to_port"] is not None

    service_def = compose_payload["services"]["web-web-a-frontend"]
    assert service_def["privileged"] is True
    assert service_def["labels"] == {"team": "blue"}
    assert service_def["build"] == "challenges/web/web-a/services/source"
