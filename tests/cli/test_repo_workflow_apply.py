from pathlib import Path

import pytest

from ctfa.cli.commands.repo.workflow.apply import command
from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.plan import WorkflowPlanner
from ctfa.models.challenge import ChallengeConfig, ChallengeService
from ctfa.models.ctf_config import CTFConfig
from ctfa.models.workflow import WorkflowConfig


class _CaptureConsole:
    def __init__(self):
        self.lines: list[str] = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(arg) for arg in args))


@pytest.fixture
def repo_with_workflows(tmp_path: Path) -> Path:
    repo_path = tmp_path / "repo"
    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    repo = ChallengeRepository.create(
        repo_path,
        CTFConfig(name="Apply CLI Repo", categories=["web"], difficulties=["easy"], starting_port=44000),
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


def test_repo_workflow_apply_command_success(monkeypatch: pytest.MonkeyPatch, repo_with_workflows: Path):
    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    command(repository_path=repo_with_workflows)

    output = "\n".join(capture.lines)
    assert "Workflow Apply" in output
    assert "1. ports (port-mapping)" in output
    assert "2. compose (docker-compose)" in output
    assert (repo_with_workflows / "port_mapping.yaml").exists()
    assert (repo_with_workflows / "compose.yml").exists()


def test_repo_workflow_apply_command_invalid_config_error(monkeypatch: pytest.MonkeyPatch, repo_with_workflows: Path):
    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    WorkflowPlanner.dump_config_file(
        repo_with_workflows,
        [WorkflowConfig(name="ports", kind="port-mapping", config={"unknown": True})],
    )

    with pytest.raises(SystemExit) as error:
        command(repository_path=repo_with_workflows)

    assert error.value.code == 1
    output = "\n".join(capture.lines)
    assert "Invalid config for workflow kind" in output
