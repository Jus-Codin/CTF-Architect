from collections.abc import Iterable

import yaml

from ctf_architect.core.action import CreateFileAction, DeploymentAction, DeploymentActionResult, UpdateFileAction
from ctf_architect.core.challenge import Challenge
from ctf_architect.core.port_mapping import load_port_mapping
from ctf_architect.core.repo import Repo
from ctf_architect.core.strategy import DeploymentStrategy, StrategyConfig
from ctf_architect.models.challenge import Service
from ctf_architect.models.port_mapping import PortMapping


def _unique_network_name(challenge: Challenge, name: str) -> str:
    return "-".join((challenge.config.category, challenge.config.folder_name, name)).lower().replace(" ", "-")


class DockerComposeConfig(StrategyConfig):
    filename: str = "compose.yml"
    project_name: str | None = None


class DockerComposeStrategy(DeploymentStrategy[DockerComposeConfig]):
    strategy_name = "docker-compose"
    config_model = DockerComposeConfig
    can_rollback = True

    def _create_challenge_networks(self, challenge: Challenge) -> dict[str, dict]:
        default_network_name = _unique_network_name(challenge, "default")

        networks = {}

        if challenge.config.networks:
            for network_name, network_config in challenge.config.networks.items():
                network_name = _unique_network_name(challenge, network_name)

                networks[network_name] = {"driver": "bridge"}

                if network_config.internal:
                    networks[network_name]["internal"] = network_config.internal

                ALLOWED_EXTRAS = {
                    "driver",
                    "driver_opts",
                    "enable_ipv4",
                    "enable_ipv6",
                    "labels",
                }

                if network_config.extras:
                    for extra in ALLOWED_EXTRAS:
                        extra_key = f"com.docker.compose.{extra}"
                        if extra_key in network_config.extras:
                            networks[network_name][extra] = network_config.extras[extra_key]

        # If default network is not defined, create it
        if default_network_name not in networks:
            networks[default_network_name] = {"driver": "bridge"}

        return networks

    def _create_compose_service(
        self,
        service: Service,
        challenge: Challenge,
        networks: list[str],
        port_mappings: list[PortMapping],
    ) -> dict:
        unique_name = service.unique_name(challenge.config)

        service_definition: dict = {
            "build": (challenge.path / service.path).relative_to(self.output_dir).as_posix(),
            "container_name": unique_name,
            "restart": "always",
        }

        ports = []

        for mapping in port_mappings:
            if mapping.to_port is not None:
                ports.append(f"{mapping.to_port}:{mapping.from_port}")
            else:
                ports.append(f"{mapping.from_port}")

        if ports:
            service_definition["ports"] = ports

        # We use networks as this actually defines the unique network name in the compose file
        if networks:
            service_definition["networks"] = {}
            for network in networks:
                service_definition["networks"][network] = {"aliases": [service.name]}
        else:
            # If no networks are defined, set network_mode to none
            service_definition["network_mode"] = "none"

        extras = service.extras.get("com.docker.compose", {}) if service.extras else {}

        for key in extras:
            if key == "restart" or key not in service_definition:
                service_definition[key] = extras[key]

        return service_definition

    def _create_compose_definition(
        self,
        challenges: Iterable[Challenge],
        port_mappings: dict[str, list[PortMapping]],
    ) -> dict:
        services = {}
        networks = {}

        for challenge in challenges:
            if challenge.config.services is None:
                continue

            # Create networks
            challenge_networks = self._create_challenge_networks(challenge)
            unused_networks = set(challenge_networks.keys())

            for service in challenge.config.services:
                unique_name = service.unique_name(challenge.config)

                # Resolve networks for the service using the following rules:
                # 1. If service.networks is defined, use those networks
                # 2. If service.networks is not defined or empty, and service.type is "internal",
                #    don't connect to any networks
                # 3. If service.networks is not defined or empty, and service.type is not "internal",
                #    connect to the default network
                service_networks = []
                if service.networks:
                    for network in service.networks:
                        network_name = _unique_network_name(challenge, network)
                        if network_name in challenge_networks:
                            service_networks.append(network_name)
                            unused_networks.discard(network_name)

                if not service_networks:
                    if service.type != "internal":
                        default_network_name = _unique_network_name(challenge, "default")
                        service_networks.append(default_network_name)
                        unused_networks.discard(default_network_name)
                    # If internal service with no networks, do not connect to any networks
                    # This is handled in _create_compose_service by setting network_mode to none

                service_port_mappings = port_mappings.get(unique_name)

                if service_port_mappings is None:
                    raise ValueError(f"Port mappings not found for service {unique_name}")

                if service.ports is not None and set(service.ports) != set(
                    pm.from_port for pm in service_port_mappings
                ):
                    raise ValueError(f"Port mappings for service {unique_name} do not match the defined ports")

                services[unique_name] = self._create_compose_service(
                    service,
                    challenge,
                    service_networks,
                    service_port_mappings,
                )

            # Remove all unused networks for the challenge
            for unused_network in unused_networks:
                del challenge_networks[unused_network]

            networks.update(challenge_networks)

        compose_definition = {}

        # Set in a specific order for readability
        if self.config.project_name:
            compose_definition["name"] = self.config.project_name

        compose_definition["networks"] = networks
        compose_definition["services"] = services

        return compose_definition

    def plan(
        self, repo: Repo, challenges: Iterable[Challenge], dependencies_actions: dict[str, list[DeploymentAction]]
    ) -> list[DeploymentAction]:
        try:
            port_mappings = load_port_mapping(repo.path)
        except FileNotFoundError:
            raise FileNotFoundError("Port mappings not found, please generate them first")

        actions: list[DeploymentAction] = []
        output_path = self.output_dir / self.config.filename

        if output_path.exists():
            with open(output_path) as f:
                existing_content = f.read()
        else:
            existing_content = ""

        new_content = yaml.dump(
            self._create_compose_definition(challenges, port_mappings),
            sort_keys=False,
        )

        if existing_content:
            action = UpdateFileAction(
                name="write-compose-file",
                strategy=self,
                target_path=output_path,
                old_content=existing_content,
                new_content=new_content,
                description="Update the existing compose.yml file with new challenge configurations.",
            )
        else:
            action = CreateFileAction(
                name="write-compose-file",
                strategy=self,
                target_path=output_path,
                content=new_content,
                description="Create a new compose.yml file with challenge configurations.",
            )

        actions.append(action)
        return actions

    def generate(
        self, repo: Repo, challenges: Iterable[Challenge], dependencies_results: dict[str, list[DeploymentActionResult]]
    ) -> list[DeploymentActionResult]:
        results: list[DeploymentActionResult] = []
        actions = self.plan(repo, challenges, {})  # No dependencies for now

        for action in actions:
            result = action.apply()
            results.append(result)

        return results
