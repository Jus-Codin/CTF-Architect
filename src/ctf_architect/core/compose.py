"""Compose integration for CTF Architect."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ctf_architect.core.exceptions import InvalidPortMappingError
from ctf_architect.core.port_mapping import load_port_mapping
from ctf_architect.core.repo import walk_challenges
from ctf_architect.models.challenge import Service
from ctf_architect.models.port_mapping import PortMapping


def get_compose_file_path(path: Path) -> Path | None:
    """Get the Compose file from the specified directory if it exists."""
    compose_files = (
        "compose.yml",
        "compose.yaml",
        "docker-compose.yml",
        "docker-compose.yaml",
    )

    for file in compose_files:
        compose_file = path / file
        if compose_file.exists():
            return compose_file

    return None


class _PortOverrides(list):
    """Custom sequence representing port overrides for a service.

    This is used to add the !override tag to the YAML output.
    """


def _construct_port_overrides(loader: yaml.SafeLoader, node: yaml.SequenceNode) -> _PortOverrides:
    return _PortOverrides(loader.construct_sequence(node))


def _represent_port_overrides(dumper: yaml.SafeDumper, data: _PortOverrides):
    return dumper.represent_sequence("!override", data)


# TODO: Maybe make a custom instance for this
yaml.add_constructor("!override", _construct_port_overrides, Loader=yaml.SafeLoader)  # type: ignore
yaml.add_representer(_PortOverrides, _represent_port_overrides, Dumper=yaml.SafeDumper)


def create_compose_service(
    service: Service,
    unique_name: str,
    network_name: str,
    challenge_path: Path,
    port_mappings: list[PortMapping],
) -> dict:
    """Create a Compose Service from a challenge service.

    This is only called for challenges that do not have a Compose file in their
    service directory.

    Args:
        service: The service object to create the Compose service for
        unique_name: The unique name for the service
        network_name: The name of the network to attach the service to
        challenge_path: The path to the challenge directory
        port_mappings: The list of port mappings for the service

    Returns:
        The Compose service as a dictionary
    """
    compose_service = {
        "container_name": unique_name,
        "networks": [network_name],
        "build": (challenge_path / service.path).as_posix(),
        "restart": "always",
    }

    ports = []

    for mapping in port_mappings:
        if mapping.to_port is not None:
            ports.append(f"{mapping.to_port}:{mapping.from_port}")
        else:
            ports.append(f"{mapping.from_port}")

    if ports:
        compose_service["ports"] = ports

    extras = service.extras if service.extras is not None else {}

    for key in extras:
        if key == "restart" or key not in compose_service:
            compose_service[key] = extras[key]

    return compose_service


def create_compose_service_override(service: Service, port_mappings: list[PortMapping]) -> dict[str, Any] | None:
    """Create a Compose Service override from a challenge service.

    This is only called for challenges that have a Compose file in their
    service directory.

    Args:
        service: The service object to create the Compose service override for
        port_mappings: The list of port mappings for the service

    Returns:
        The Compose service override as a dictionary or None if there are no overrides
    """
    extras = service.extras if service.extras is not None else {}

    compose_service = {**extras}

    ports = _PortOverrides()

    for mapping in port_mappings:
        if mapping.to_port is not None:
            ports.append(f"{mapping.to_port}:{mapping.from_port}")
        else:
            ports.append(f"{mapping.from_port}")

    if ports:
        compose_service["ports"] = ports

    return compose_service or None


def create_compose_dicts() -> tuple[dict, dict | None]:
    """Create a dictionary for the Compose and Compose override files."""
    try:
        port_mapping = load_port_mapping()
    except FileNotFoundError:
        raise FileNotFoundError("Port mappings not found, please generate them first")

    # Compose file elements
    include = []
    services = {}
    networks = {}

    # Compose override file
    # This is used to override the ports for services added via the includes
    overrides = {}

    for challenge in walk_challenges():
        if challenge.services is not None:
            network_name = challenge.network_name

            # Check if the challenge has a Compose file in its service directory
            compose_file = get_compose_file_path(challenge.repo_path / "service")

            if compose_file is None:
                if network_name not in networks:
                    networks[network_name] = {"driver": "bridge"}
            else:
                # NOTE: We do not actually validate the Compose file here
                #       Though we actually require it to have the correct services and
                #       Service names, we do not check for that here
                include.append(compose_file.as_posix())

            for service in challenge.services:
                unique_name = service.unique_name(challenge)

                if unique_name not in port_mapping:
                    raise InvalidPortMappingError(f"Port mapping not found for service {unique_name}")

                if set(service.ports_list) != set(port.from_port for port in port_mapping[unique_name]):
                    raise InvalidPortMappingError(f"Port mapping mismatch for service {unique_name}")

                if compose_file is None:
                    services[unique_name] = create_compose_service(
                        service,
                        unique_name,
                        network_name,
                        challenge.repo_path,
                        port_mapping[unique_name],
                    )
                else:
                    override = create_compose_service_override(service, port_mapping[unique_name])

                    if override is not None:
                        overrides[unique_name] = override

    return (
        {"include": include, "services": services, "networks": networks},
        {"services": overrides} if overrides else None,
    )


def create_compose_files() -> None:
    """Creates a compose.yml and compose.override.yml file for all challenges."""
    compose, override = create_compose_dicts()

    with open("compose.yml", "w") as file:
        yaml.dump(compose, file)

    if override is not None:
        with open("compose.override.yml", "w") as file:
            yaml.dump(override, file)


def update_compose_files() -> None:
    """Updates the compose.yml and compose.override.yml files for all challenges.

    NOTE: This will only not overwrite extra configurations in the compose files.
    Existing configurations that were generated by CTF Architect and manually changed will be lost.
    """
    if not Path("compose.yml").exists():
        raise FileNotFoundError("compose.yml not found")

    with open("compose.yml") as f:
        compose = yaml.safe_load(f)

    if Path("compose.override.yml").exists():
        with open("compose.override.yml") as f:
            overrides = yaml.safe_load(f)
    else:
        overrides = None

    # Create new compose files
    new_compose, new_overrides = create_compose_dicts()

    # Update the existing compose files
    compose["include"] = new_compose["include"]
    compose["services"].update(new_compose["services"])
    compose["networks"].update(new_compose["networks"])

    if new_overrides is not None:
        if overrides is None:
            overrides = new_overrides
        else:
            overrides["services"].update(new_overrides["services"])

    with open("compose.yml", "w") as f:
        yaml.safe_dump(compose, f)

    if overrides is not None:
        with open("compose.override.yml", "w") as f:
            yaml.safe_dump(overrides, f)
