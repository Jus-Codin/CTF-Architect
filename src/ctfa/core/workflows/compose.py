from __future__ import annotations

from io import StringIO
from pathlib import Path

from pydantic import TypeAdapter

from ctfa.constants import PORT_MAPPING_FILE
from ctfa.core.workflow.actions import CreateFileAction, UpdateFileAction, WorkflowAction
from ctfa.core.workflow.base import (
    WorkflowKind,
    WorkflowKindConfig,
    WorkflowKindPlanResult,
    WorkflowPlanContext,
    register_workflow_kind,
)
from ctfa.core.workflow.outputs import (
    ComposeWorkflowOutput,
    PortMappingEntry,
    PortMappingWorkflowOutput,
    WorkflowOutput,
    find_output,
)
from ctfa.models.challenge import ChallengeConfig, ChallengeService
from ctfa.utils import yaml
from ctfa.version import is_supported_port_mapping_version


def service_sort_key(challenge: ChallengeConfig, service: ChallengeService) -> tuple[str, str, str, str]:
    return (challenge.category, challenge.folder_name, challenge.id, service.name)


class ComposeWorkflowConfig(WorkflowKindConfig):
    filename: str = "compose.yml"
    project_name: str | None = None
    port_mapping_file: str = PORT_MAPPING_FILE


@register_workflow_kind
class ComposeWorkflowKind(WorkflowKind):
    kind_name = "docker-compose"
    config_model = ComposeWorkflowConfig

    @staticmethod
    def _network_name(challenge: ChallengeConfig, network_name: str) -> str:
        return f"{challenge.category}-{challenge.id}-{network_name}".lower().replace(" ", "-")

    @staticmethod
    def _parse_port_mapping_payload(payload: object) -> dict[str, list[PortMappingEntry]]:
        if not isinstance(payload, dict):
            raise ValueError("Port mapping file must contain a mapping object")

        version = payload.get("version")
        if isinstance(version, (int, float)):
            version = str(version)
        if not isinstance(version, str) or not is_supported_port_mapping_version(version):
            raise ValueError("Port mapping file has an unsupported or missing version")

        mapping = payload.get("mapping")
        if not isinstance(mapping, dict):
            raise ValueError("Port mapping file must include a dictionary `mapping` field")

        return TypeAdapter(dict[str, list[PortMappingEntry]]).validate_python(mapping)

    def _load_port_mapping_file(
        self,
        context: WorkflowPlanContext,
        config: ComposeWorkflowConfig,
    ) -> dict[str, list[PortMappingEntry]]:
        mapping_path = context.repository_path / config.port_mapping_file
        if not mapping_path.is_file():
            raise ValueError(
                "docker-compose workflow requires either a dependency on a prior port-mapping workflow "
                f"or an existing {config.port_mapping_file} file"
            )

        with mapping_path.open("r", encoding="utf-8") as handle:
            payload = yaml.load(handle)

        return self._parse_port_mapping_payload(payload)

    def _resolve_port_mapping(
        self,
        context: WorkflowPlanContext,
        config: ComposeWorkflowConfig,
    ) -> dict[str, list[PortMappingEntry]]:
        if not any(challenge.services for challenge in context.selected_challenges):
            return {}

        for workflow_name in context.workflow.depends_on:
            output = find_output(context.prior_step_outputs.get(workflow_name, []), "port_mapping")
            if isinstance(output, PortMappingWorkflowOutput):
                return {service_name: [entry for entry in entries] for service_name, entries in output.mapping.items()}

        return self._load_port_mapping_file(context, config)

    def _build_service(
        self,
        challenge: ChallengeConfig,
        service: ChallengeService,
        mapping: list[PortMappingEntry],
        service_networks: list[str],
    ) -> tuple[dict, list[str]]:
        service_definition: dict = {
            "build": (challenge.repository_path / service.path).as_posix(),
            "container_name": service.unique_name(challenge),
            "restart": "always",
        }
        warnings: list[str] = []

        if mapping:
            ports = [
                f"{entry.to_port}:{entry.from_port}" if entry.to_port is not None else f"{entry.from_port}"
                for entry in mapping
            ]
            service_definition["ports"] = ports

        if service_networks:
            service_definition["networks"] = {name: {"aliases": [service.name]} for name in service_networks}
        else:
            service_definition["network_mode"] = "none"

        annotations = service.annotations or {}
        if "privileged" in annotations:
            service_definition["privileged"] = bool(annotations["privileged"])

        extras = annotations.get("ctfa.compose.extras")
        if extras is not None:
            if not isinstance(extras, dict):
                warnings.append(
                    f"Service {service.unique_name(challenge)} has invalid ctfa.compose.extras annotation; expected a dict."
                )
            else:
                disallowed = {"build", "container_name", "restart", "ports", "networks", "network_mode"}
                for key, value in extras.items():
                    if key in disallowed:
                        warnings.append(
                            f"Service {service.unique_name(challenge)} ignored ctfa.compose.extras key '{key}'."
                        )
                        continue
                    service_definition[key] = value

        return service_definition, warnings

    def _compose_definition(
        self,
        *,
        challenges: list[ChallengeConfig],
        port_mapping: dict[str, list[PortMappingEntry]],
        config: ComposeWorkflowConfig,
    ) -> tuple[dict, list[str]]:
        services: dict[str, dict] = {}
        networks: dict[str, dict] = {}
        warnings: list[str] = []

        ordered_challenges = sorted(
            challenges, key=lambda challenge: (challenge.category, challenge.folder_name, challenge.id)
        )

        for challenge in ordered_challenges:
            challenge_networks: dict[str, dict] = {}
            if challenge.networks:
                for network_name, network_config in sorted(challenge.networks.items()):
                    unique_network_name = self._network_name(challenge, network_name)
                    challenge_networks[unique_network_name] = {"driver": "bridge"}
                    if network_config.internal:
                        challenge_networks[unique_network_name]["internal"] = True

            default_network = challenge.default_network_name
            challenge_networks.setdefault(default_network, {"driver": "bridge"})

            for service in sorted(challenge.services or [], key=lambda item: service_sort_key(challenge, item)):
                unique_service_name = service.unique_name(challenge)
                service_mapping = port_mapping.get(unique_service_name)
                if service_mapping is None:
                    raise ValueError(f"Missing port mapping for service {unique_service_name}")

                service_networks: list[str] = []
                if service.networks:
                    service_networks = [
                        self._network_name(challenge, network_name)
                        for network_name in sorted(service.networks)
                        if self._network_name(challenge, network_name) in challenge_networks
                    ]
                elif service.type != "internal":
                    service_networks = [default_network]

                for network in service_networks:
                    networks[network] = challenge_networks[network]

                service_definition, service_warnings = self._build_service(
                    challenge,
                    service,
                    service_mapping,
                    service_networks,
                )
                services[unique_service_name] = service_definition
                warnings.extend(service_warnings)

        compose: dict = {}
        if config.project_name:
            compose["name"] = config.project_name

        compose["networks"] = {name: networks[name] for name in sorted(networks)}
        compose["services"] = {name: services[name] for name in sorted(services)}
        return compose, warnings

    def plan_step(self, context: WorkflowPlanContext, config: WorkflowKindConfig) -> WorkflowKindPlanResult:
        assert isinstance(config, ComposeWorkflowConfig)

        mapping = self._resolve_port_mapping(context, config)
        compose_definition, warnings = self._compose_definition(
            challenges=context.selected_challenges,
            port_mapping=mapping,
            config=config,
        )

        output_path = (
            context.workflow.output_dir / config.filename if context.workflow.output_dir else Path(config.filename)
        )
        target_path = context.repository_path / output_path

        buffer = StringIO()
        yaml.dump(compose_definition, buffer)
        content = buffer.getvalue()
        outputs: list[WorkflowOutput] = [ComposeWorkflowOutput(compose=compose_definition)]
        message = "; ".join(warnings) if warnings else None

        if target_path.exists():
            old_content = target_path.read_text(encoding="utf-8")
            if old_content == content:
                return WorkflowKindPlanResult(
                    actions=[],
                    outputs=outputs,
                    message=message or "No changes needed",
                )

            action: WorkflowAction = UpdateFileAction(
                name=f"update-{config.filename}",
                description="Update generated docker compose output",
                target_path=output_path,
                old_content=old_content,
                new_content=content,
            )
            return WorkflowKindPlanResult(actions=[action], outputs=outputs, message=message)

        action = CreateFileAction(
            name=f"create-{config.filename}",
            description="Create generated docker compose output",
            target_path=output_path,
            content=content,
        )
        return WorkflowKindPlanResult(actions=[action], outputs=outputs, message=message)
