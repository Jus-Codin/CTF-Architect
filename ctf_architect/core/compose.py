"""
Compose integration for CTF Architect
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.mapping import load_port_mapping
from ctf_architect.core.models import PortMapping, Service


def sanitize_name(name: str) -> str:
    """
    Sanitize a name for a service or network.

    All non alphanumeric characters are removed, letters are converted to lowercase,
    and spaces are replaced with dashes
    """
    return "".join(c for c in name.lower().replace(" ", "-") if c.isalnum())


def get_compose_file(path: Path) -> Path | None:
    """
    Get the Compose file from the specified directory if it exists.
    """
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


class PortOverrides(list):
    """
    Custom sequence representing port overrides for a service.

    This is used to add the !override tag to the YAML output.
    """


def construct_port_overrides(loader: yaml.SafeLoader, node: yaml.Node) -> PortOverrides:
    return PortOverrides(loader.construct_sequence(node))


def represent_port_overrides(dumper: yaml.SafeDumper, data: PortOverrides):
    return dumper.represent_sequence("!override", data)


yaml.add_constructor("!override", construct_port_overrides, Loader=yaml.SafeLoader)
yaml.add_representer(PortOverrides, represent_port_overrides, Dumper=yaml.SafeDumper)


def create_compose_service(
    service: Service,
    challenge_name: str,
    network_name: str,
    challenge_path: Path,
    port_mappings: list[PortMapping],
) -> dict:
    """
    Create a Compose Service from a challenge service

    This is only called for challenges that do not have a Compose file in their
    service directory.
    """

    compose_service = {
        "container_name": sanitize_name(f"{challenge_name}-{service.name}"),
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


def create_compose_service_override(
    service: Service, port_mappings: list[PortMapping]
) -> dict:
    """
    Create a Compose Service override from a challenge service

    This is only called for challenges that have a Compose file in their
    service directory.
    """

    extras = service.extras if service.extras is not None else {}

    compose_service = {**extras}

    ports = PortOverrides()

    for mapping in port_mappings:
        if mapping.to_port is not None:
            ports.append(f"{mapping.to_port}:{mapping.from_port}")
        else:
            ports.append(f"{mapping.from_port}")

    if ports:
        compose_service["ports"] = ports

    return compose_service


def create_compose_dicts() -> tuple[dict, dict]:
    """
    Create a dictionary for the compose.yml and compose.override.yml files
    """

    try:
        port_mapping = load_port_mapping()
    except FileNotFoundError:
        raise ValueError("Port mappings not found, please generate them first")

    # Compose file elements
    include = []
    services = {}
    networks = {}

    # Compose override file
    # This is used to override the ports for services added via the includes
    overrides = {}

    for challenge in walk_challenges():
        if challenge.services is not None:
            # Check if the challenge has a Compose file in its service directory
            compose_file = get_compose_file(challenge.full_path / "service")

            if compose_file is None:
                network_name = f"{sanitize_name(challenge.name)}-network"

                if network_name not in networks:
                    networks[network_name] = {}
            else:
                include.append(compose_file.as_posix())

            for service in challenge.services:
                if service.name not in port_mapping.mapping:
                    raise ValueError(
                        f"Port mapping not found for service: {service.name}"
                    )

                # Check if all ports are mapped
                if set(service.ports_list) != set(
                    port.from_port for port in port_mapping.mapping[service.name]
                ):
                    raise ValueError(
                        f'Port mapping mismatch for service "{service.name}"'
                    )

                if compose_file is None:
                    services[service.name] = create_compose_service(
                        service,
                        challenge.name,
                        network_name,
                        challenge.full_path,
                        port_mapping.mapping[service.name],
                    )
                else:
                    # It is possible for an empty dictionary to be created,
                    # but I don't think it will be a problem, sorry future me if it is
                    overrides[service.name] = create_compose_service_override(
                        service, port_mapping.mapping[service.name]
                    )

    return (
        {"include": include, "services": services, "networks": networks},
        {"services": overrides},
    )


def create_compose_files() -> None:
    """
    Creates a compose.yml and compose.override.yml file for all challenges
    """

    compose, overrides = create_compose_dicts()

    with open("compose.yml", "w") as f:
        yaml.safe_dump(compose, f)

    with open("compose.override.yml", "w") as f:
        yaml.safe_dump(overrides, f)


def update_compose_files() -> None:
    """
    Updates existing compose files with new configurations while keeping custom configurations

    NOTE: This will only not overwrite extra configurations in the compose files.
    Existing configurations that were generated by CTF Architect and manually changed will be lost.
    """

    if not Path("compose.yml").exists():
        raise FileNotFoundError("compose.yml does not exist")
    elif not Path("compose.override.yml").exists():
        raise FileNotFoundError("compose.override.yml does not exist")

    # Try to load the existing compose files
    try:
        with open("compose.yml", "r") as f:
            compose = yaml.safe_load(f)
        with open("compose.override.yml", "r") as f:
            overrides = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Error loading existing compose files: {e}") from e

    # Create new compose files
    new_compose, new_overrides = create_compose_dicts()

    # Update the existing compose files
    compose["include"] = new_compose["include"]
    compose["services"].update(new_compose["services"])
    compose["networks"].update(new_compose["networks"])

    overrides["services"].update(new_overrides["services"])

    with open("compose.yml", "w") as f:
        yaml.safe_dump(compose, f)

    with open("compose.override.yml", "w") as f:
        yaml.safe_dump(overrides, f)
