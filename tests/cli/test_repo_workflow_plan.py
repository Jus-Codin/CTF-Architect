from pathlib import Path

import pytest

from ctfa.cli.commands.repo.workflow.plan import command
from ctfa.core.challenge import Challenge
from ctfa.core.repository import ChallengeRepository
from ctfa.core.workflow.plan import WorkflowPlanner
from ctfa.models.challenge import ChallengeConfig
from ctfa.models.ctf_config import CTFConfig
from ctfa.models.workflow import SelectorRule, Selectors, WorkflowConfig


class _CaptureConsole:
    def __init__(self):
        self.lines: list[str] = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(arg) for arg in args))


@pytest.fixture
def repo_with_challenges(tmp_path: Path) -> Path:
    repo_path = tmp_path / "repo"
    ctf_config = CTFConfig(
        name="Stage2 Repo",
        categories=["crypto", "web"],
        difficulties=["easy", "hard"],
    )
    repo = ChallengeRepository.create(repo_path, ctf_config)

    source_path = tmp_path / "source"
    source_path.mkdir(parents=True)

    crypto_challenge = ChallengeConfig(
        id="crypto-one",
        name="Crypto One",
        description="Crypto challenge",
        category="crypto",
        difficulty="easy",
        author="tester",
    )
    web_challenge = ChallengeConfig(
        id="web-one",
        name="Web One",
        description="Web challenge",
        category="web",
        difficulty="hard",
        author="tester",
    )

    challenge_a = Challenge.package(crypto_challenge, source_path, as_subfolder=True)
    challenge_b = Challenge.package(web_challenge, source_path, as_subfolder=True)

    repo.add_challenge(challenge_a, preserve_original=True)
    repo.add_challenge(challenge_b, preserve_original=True)

    return repo_path


def test_repo_workflow_plan_command_success(monkeypatch: pytest.MonkeyPatch, repo_with_challenges: Path):
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping", selectors=Selectors(include="*")),
        WorkflowConfig(
            name="compose",
            kind="docker-compose",
            depends_on=["ports"],
            selectors=Selectors(include=[{"category": SelectorRule(value="web")}]),
        ),
    ]
    WorkflowPlanner.dump_config_file(repo_with_challenges, workflows)

    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    command(repository_path=repo_with_challenges)

    output = "\n".join(capture.lines)
    assert "Workflow Plan" in output
    assert "1. ports (port-mapping)" in output
    assert "2. compose (docker-compose)" in output
    assert "selected challenges: 2" in output
    assert "selected challenges: 1" in output


def test_repo_workflow_plan_command_dependency_error(monkeypatch: pytest.MonkeyPatch, repo_with_challenges: Path):
    workflows = [
        WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
    ]
    WorkflowPlanner.dump_config_file(repo_with_challenges, workflows)

    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    with pytest.raises(SystemExit) as error:
        command(repository_path=repo_with_challenges)

    assert error.value.code == 1
    output = "\n".join(capture.lines)
    assert "depends on unknown workflow" in output


def test_repo_workflow_plan_command_include_filter(monkeypatch: pytest.MonkeyPatch, repo_with_challenges: Path):
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping", selectors=Selectors(include="*")),
        WorkflowConfig(
            name="ports-alt",
            kind="port-mapping",
            selectors=Selectors(include="*"),
            config={"filename": "alt_port_mapping.yaml"},
        ),
    ]
    WorkflowPlanner.dump_config_file(repo_with_challenges, workflows)

    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    command(repository_path=repo_with_challenges, include_workflows=["ports-alt"])

    output = "\n".join(capture.lines)
    assert "1. ports-alt (port-mapping)" in output
    assert "ports (port-mapping)" not in output


def test_repo_workflow_plan_command_unknown_filter_error(monkeypatch: pytest.MonkeyPatch, repo_with_challenges: Path):
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping", selectors=Selectors(include="*")),
    ]
    WorkflowPlanner.dump_config_file(repo_with_challenges, workflows)

    capture = _CaptureConsole()
    monkeypatch.setattr("ctfa.cli.ui.console.console", capture)

    with pytest.raises(SystemExit) as error:
        command(repository_path=repo_with_challenges, include_workflows=["missing"])

    assert error.value.code == 1
    output = "\n".join(capture.lines)
    assert "Unknown workflow name(s) in include filter" in output
