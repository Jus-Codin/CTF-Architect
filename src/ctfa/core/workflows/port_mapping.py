from __future__ import annotations

import hashlib
import random
import secrets
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import Field

from ctfa.constants import PORT_MAPPING_FILE
from ctfa.core.workflow.actions import CreateFileAction, UpdateFileAction, WorkflowAction
from ctfa.core.workflow.base import (
    WorkflowKind,
    WorkflowKindConfig,
    WorkflowKindPlanResult,
    WorkflowPlanContext,
    register_workflow_kind,
)
from ctfa.core.workflow.outputs import PortMappingEntry, PortMappingWorkflowOutput, WorkflowOutput
from ctfa.models.challenge import ChallengeConfig
from ctfa.utils import yaml
from ctfa.version import PORT_MAPPING_SPEC_VERSION


class PortMappingStrategy(StrEnum):
    SEQUENTIAL = "sequential"
    CATEGORY = "category"
    RANDOM = "random"
    HASH = "hash"


class PortMappingConfig(WorkflowKindConfig):
    filename: str = PORT_MAPPING_FILE
    starting_port: int | None = None
    separation: int | None = 1000
    max_port: int = Field(default=65535, ge=1, le=65535)
    strategy: PortMappingStrategy = Field(default=PortMappingStrategy.CATEGORY)
    preserve_existing: bool = True
    random_seed: int | str | None = None


@register_workflow_kind
class PortMappingWorkflowKind(WorkflowKind):
    kind_name = "port-mapping"
    config_model = PortMappingConfig

    @staticmethod
    def _serialize_mapping(mapping: dict[str, list[dict[str, int | None]]]) -> str:
        payload = {
            "version": str(PORT_MAPPING_SPEC_VERSION),
            "mapping": {key: mapping[key] for key in sorted(mapping)},
        }
        buffer = StringIO()
        yaml.dump(payload, buffer)
        return buffer.getvalue()

    @staticmethod
    def _service_sort_key(challenge: ChallengeConfig, service_name: str) -> tuple[str, str, str, str]:
        return (challenge.category, challenge.folder_name, challenge.id, service_name)

    @staticmethod
    def _normalize_mapping(mapping: dict[str, list[dict[str, int | None]]]) -> dict[str, list[PortMappingEntry]]:
        return {
            service_name: [PortMappingEntry.model_validate(entry) for entry in entries]
            for service_name, entries in mapping.items()
        }

    @staticmethod
    def _load_existing_mapping(path: Path) -> dict[str, list[dict[str, int | None]]]:
        if not path.is_file():
            return {}

        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.load(handle) or {}

        mapping = payload.get("mapping")
        if not isinstance(mapping, dict):
            return {}

        parsed: dict[str, list[dict[str, int | None]]] = {}
        for service_name, entries in mapping.items():
            if not isinstance(service_name, str) or not isinstance(entries, list):
                continue

            parsed_entries: list[dict[str, int | None]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                from_port = entry.get("from_port")
                to_port = entry.get("to_port")
                if isinstance(from_port, int) and (to_port is None or isinstance(to_port, int)):
                    parsed_entries.append({"from_port": from_port, "to_port": to_port})

            parsed[service_name] = parsed_entries

        return parsed

    @staticmethod
    def _public_port_candidates(starting_port: int, max_port: int) -> range:
        return range(starting_port, max_port + 1)

    @staticmethod
    def _service_identity(challenge: ChallengeConfig, service_name: str) -> str:
        return f"{challenge.category}:{challenge.folder_name}:{challenge.id}:{service_name}"

    @staticmethod
    def _generate_seed() -> int:
        return secrets.randbits(64)

    def _generate_mapping_random(
        self,
        *,
        challenges: list[ChallengeConfig],
        starting_port: int,
        max_port: int,
        random_seed: int | str | None,
        existing_mapping: dict[str, list[dict[str, int | None]]],
    ) -> dict[str, list[dict[str, int | None]]]:
        available_ports = len(self._public_port_candidates(starting_port, max_port))
        if available_ports <= 0:
            raise ValueError("No ports available for random allocation")

        rng = random.Random(str(random_seed) if random_seed is not None else self._generate_seed())
        allocated_ports = {
            entry["to_port"]
            for entries in existing_mapping.values()
            for entry in entries
            if entry.get("to_port") is not None
        }
        mapping: dict[str, list[dict[str, int | None]]] = {}

        ordered_challenges = sorted(challenges, key=lambda c: (c.category, c.folder_name, c.id))
        for challenge in ordered_challenges:
            services = sorted(
                challenge.services or [],
                key=lambda service: self._service_sort_key(challenge, service.name),
            )
            for service in services:
                unique_name = service.unique_name(challenge)
                service_mappings: list[dict[str, int | None]] = []
                existing_entries = existing_mapping.get(unique_name, [])
                existing_lookup = {
                    entry["from_port"]: entry.get("to_port")
                    for entry in existing_entries
                    if isinstance(entry.get("from_port"), int)
                }
                for service_port in service.ports:
                    if service.type == "internal":
                        service_mappings.append({"from_port": service_port, "to_port": None})
                        continue

                    preserved_port = existing_lookup.get(service_port)
                    if preserved_port is not None:
                        service_mappings.append({"from_port": service_port, "to_port": preserved_port})
                        continue

                    if available_ports <= 0:
                        raise ValueError("Not enough ports available to generate randomized port mappings")

                    while True:
                        candidate_port = rng.randint(starting_port, max_port)
                        if candidate_port not in allocated_ports:
                            allocated_ports.add(candidate_port)
                            break

                    service_mappings.append({"from_port": service_port, "to_port": candidate_port})
                    available_ports -= 1

                mapping[unique_name] = service_mappings

        return mapping

    def _generate_mapping_hash(
        self,
        *,
        challenges: list[ChallengeConfig],
        starting_port: int,
        max_port: int,
        existing_mapping: dict[str, list[dict[str, int | None]]],
    ) -> dict[str, list[dict[str, int | None]]]:
        pool = list(self._public_port_candidates(starting_port, max_port))
        if len(pool) <= 0:
            raise ValueError("No ports available for hashed allocation")

        used_ports = {
            entry["to_port"]
            for entries in existing_mapping.values()
            for entry in entries
            if entry.get("to_port") is not None
        }
        mapping: dict[str, list[dict[str, int | None]]] = {}

        ordered_challenges = sorted(challenges, key=lambda c: (c.category, c.folder_name, c.id))
        for challenge in ordered_challenges:
            services = sorted(
                challenge.services or [],
                key=lambda service: self._service_sort_key(challenge, service.name),
            )
            for service in services:
                unique_name = service.unique_name(challenge)
                service_mappings: list[dict[str, int | None]] = []
                existing_entries = existing_mapping.get(unique_name, [])
                existing_lookup = {
                    entry["from_port"]: entry.get("to_port")
                    for entry in existing_entries
                    if isinstance(entry.get("from_port"), int)
                }
                for service_port in service.ports:
                    if service.type == "internal":
                        service_mappings.append({"from_port": service_port, "to_port": None})
                        continue

                    preserved_port = existing_lookup.get(service_port)
                    if preserved_port is not None:
                        service_mappings.append({"from_port": service_port, "to_port": preserved_port})
                        continue

                    identity = f"{self._service_identity(challenge, service.name)}:{service_port}"
                    start_index = int(hashlib.sha256(identity.encode("utf-8")).hexdigest(), 16) % len(pool)
                    allocated_port = None
                    for offset in range(len(pool)):
                        candidate = pool[(start_index + offset) % len(pool)]
                        if candidate not in used_ports:
                            allocated_port = candidate
                            used_ports.add(candidate)
                            break

                    if allocated_port is None:
                        raise ValueError("Not enough ports available to generate hashed port mappings")

                    service_mappings.append({"from_port": service_port, "to_port": allocated_port})

                mapping[unique_name] = service_mappings

        return mapping

    def _generate_mapping(
        self,
        *,
        challenges: list[ChallengeConfig],
        starting_port: int,
        separation: int | None,
        max_port: int,
        strategy: PortMappingStrategy,
        existing_mapping: dict[str, list[dict[str, int | None]]],
        random_seed: int | str | None,
    ) -> dict[str, list[dict[str, int | None]]]:
        if strategy == PortMappingStrategy.RANDOM:
            return self._generate_mapping_random(
                challenges=challenges,
                starting_port=starting_port,
                max_port=max_port,
                random_seed=random_seed,
                existing_mapping=existing_mapping,
            )

        if strategy == PortMappingStrategy.HASH:
            return self._generate_mapping_hash(
                challenges=challenges,
                starting_port=starting_port,
                max_port=max_port,
                existing_mapping=existing_mapping,
            )

        port = starting_port
        mapping: dict[str, list[dict[str, int | None]]] = {}

        ordered_challenges = sorted(challenges, key=lambda c: (c.category, c.folder_name, c.id))
        current_category: str | None = None
        for challenge in ordered_challenges:
            if (
                strategy == PortMappingStrategy.CATEGORY
                and separation
                and current_category is not None
                and challenge.category != current_category
            ):
                if port % separation:
                    port += separation - (port % separation)
            current_category = challenge.category

            services = sorted(
                challenge.services or [],
                key=lambda service: self._service_sort_key(challenge, service.name),
            )
            has_public_service = False

            for service in services:
                unique_name = service.unique_name(challenge)
                if unique_name in mapping:
                    raise ValueError(f"Duplicate service name generated: {unique_name}")

                service_mappings: list[dict[str, int | None]] = []
                existing_entries = existing_mapping.get(unique_name, [])
                existing_lookup = {
                    entry["from_port"]: entry.get("to_port")
                    for entry in existing_entries
                    if isinstance(entry.get("from_port"), int)
                }

                for service_port in service.ports:
                    if service.type == "internal":
                        service_mappings.append({"from_port": service_port, "to_port": None})
                        continue

                    preserved_port = existing_lookup.get(service_port)
                    if preserved_port is not None:
                        has_public_service = True
                        service_mappings.append({"from_port": service_port, "to_port": preserved_port})
                        continue

                    if port > max_port:
                        raise ValueError("Not enough ports available to generate port mappings")

                    has_public_service = True
                    service_mappings.append({"from_port": service_port, "to_port": port})
                    port += 1

                mapping[unique_name] = service_mappings

            if strategy != PortMappingStrategy.CATEGORY and separation and has_public_service and (port % separation):
                port += separation - (port % separation)

            if port > max_port:
                raise ValueError("Not enough ports available to generate port mappings")

        return mapping

    def plan_step(self, context: WorkflowPlanContext, config: WorkflowKindConfig) -> WorkflowKindPlanResult:
        assert isinstance(config, PortMappingConfig)

        output_path = (
            context.workflow.output_dir / config.filename if context.workflow.output_dir else Path(config.filename)
        )
        target_path = context.repository_path / output_path
        existing_mapping = self._load_existing_mapping(target_path) if config.preserve_existing else {}

        if not any(challenge.services for challenge in context.selected_challenges):
            mapping: dict[str, list[dict[str, int | None]]] = {}
            content = self._serialize_mapping(mapping)
            outputs: list[WorkflowOutput] = [PortMappingWorkflowOutput(mapping={})]

            if target_path.exists():
                old_content = target_path.read_text(encoding="utf-8")
                if old_content == content:
                    return WorkflowKindPlanResult(actions=[], outputs=outputs, message="No changes needed")

                action: WorkflowAction = UpdateFileAction(
                    name=f"update-{config.filename}",
                    description="Update generated port mapping output",
                    target_path=output_path,
                    old_content=old_content,
                    new_content=content,
                )
                return WorkflowKindPlanResult(actions=[action], outputs=outputs)

            action = CreateFileAction(
                name=f"create-{config.filename}",
                description="Create generated port mapping output",
                target_path=output_path,
                content=content,
            )
            return WorkflowKindPlanResult(actions=[action], outputs=outputs)

        starting_port = config.starting_port
        if starting_port is None:
            from ctfa.core.repository import ChallengeRepository

            repo = ChallengeRepository.load_repository(context.repository_path)
            if repo.ctf_config.starting_port is None:
                raise ValueError(
                    "Port-mapping workflow requires either workflow config `starting_port` "
                    "or repository `starting_port` in ctf_config.yaml"
                )
            starting_port = repo.ctf_config.starting_port

        mapping = self._generate_mapping(
            challenges=context.selected_challenges,
            starting_port=starting_port,
            separation=config.separation,
            max_port=config.max_port,
            strategy=config.strategy,
            existing_mapping=existing_mapping,
            random_seed=config.random_seed,
        )
        content = self._serialize_mapping(mapping)
        outputs: list[WorkflowOutput] = [PortMappingWorkflowOutput(mapping=self._normalize_mapping(mapping))]

        if target_path.exists():
            old_content = target_path.read_text(encoding="utf-8")
            if old_content == content:
                return WorkflowKindPlanResult(actions=[], outputs=outputs, message="No changes needed")

            action = UpdateFileAction(
                name=f"update-{config.filename}",
                description="Update generated port mapping output",
                target_path=output_path,
                old_content=old_content,
                new_content=content,
            )
            return WorkflowKindPlanResult(actions=[action], outputs=outputs)

        action = CreateFileAction(
            name=f"create-{config.filename}",
            description="Create generated port mapping output",
            target_path=output_path,
            content=content,
        )
        return WorkflowKindPlanResult(actions=[action], outputs=outputs)
