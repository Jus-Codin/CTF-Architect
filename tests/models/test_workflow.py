from pathlib import Path

import pytest

from ctfa.models.workflow import SelectorRule, WorkflowConfig, WorkflowsConfigFile
from ctfa.version import WORKFLOWS_SPEC_VERSION


def test_workflow_config_initialization():
    workflow = WorkflowConfig(
        name="compose",
        kind="docker-compose",
        config={"file": "compose.yaml"},
        output_dir=Path("artifacts"),
        depends_on=["ports"],
    )

    assert workflow.name == "compose"
    assert workflow.kind == "docker-compose"
    assert workflow.config == {"file": "compose.yaml"}
    assert workflow.output_dir == Path("artifacts")
    assert workflow.depends_on == ["ports"]


def test_workflow_config_rejects_absolute_output_dir():
    with pytest.raises(ValueError, match="Output directory must be a relative path"):
        WorkflowConfig(name="compose", kind="docker-compose", output_dir=Path("/absolute/path"))


def test_workflows_config_file_from_workflows():
    workflows = [
        WorkflowConfig(name="ports", kind="port-mapping"),
        WorkflowConfig(name="compose", kind="docker-compose", depends_on=["ports"]),
    ]

    config_file = WorkflowsConfigFile.from_workflows(workflows)
    assert config_file.version == str(WORKFLOWS_SPEC_VERSION)
    assert config_file.workflows == workflows


def test_workflows_config_file_invalid_version():
    data = {
        "version": "99.99",
        "workflows": [{"name": "ports", "kind": "port-mapping"}],
    }

    with pytest.raises(ValueError, match='Unsupported Workflows specification version: "99.99"'):
        WorkflowsConfigFile.model_validate(data)


def test_selector_rule_rejects_invalid_regex_pattern():
    with pytest.raises(ValueError):
        SelectorRule(pattern="(")
