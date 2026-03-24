from __future__ import annotations

from typing import Literal

from pydantic import Field

from ctfa.models._base import Model


class PortMappingEntry(Model):
    from_port: int
    to_port: int | None


class WorkflowOutput(Model):
    output_type: str


class PortMappingWorkflowOutput(WorkflowOutput):
    output_type: Literal["port_mapping"] = "port_mapping"
    mapping: dict[str, list[PortMappingEntry]] = Field(default_factory=dict)


class ComposeWorkflowOutput(WorkflowOutput):
    output_type: Literal["compose"] = "compose"
    compose: dict = Field(default_factory=dict)


def find_output(outputs: list[WorkflowOutput], output_type: str) -> WorkflowOutput | None:
    for output in outputs:
        if output.output_type == output_type:
            return output
    return None
