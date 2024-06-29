"""
Functions for creating a docker compose file for services needing hosting
"""

from __future__ import annotations

from pathlib import Path

from yaml import safe_dump

from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.config import load_config
from ctf_architect.core.mapping import load_port_mapping
from ctf_architect.core.models import Service


def challenge_name_to_network_name(challenge_name: str) -> str:
    """
    Convert a challenge name to a network name.

    All non alphanumeric characters are removed, and spaces are replaced with dashes
    """
    name = "".join(c for c in challenge_name.lower().replace(" ", "-") if c.isalnum())
    return f"{name}-network"


def create_compose_dict(
    service: Service, challenge_path: Path, network_name: str, host_port: int | None
) -> dict:
    """
    Create a docker compose service from a challenge service
    """

    d = {"container_name": service.name, "networks": [network_name]}

    if host_port is not None:
        d["ports"] = [f"{host_port}:{service.port}"]

    service_docker_compose = challenge_path / "service" / "docker-compose.yml"

    if service_docker_compose.exists():
        d["extends"] = {
            "file": service_docker_compose.as_posix(),
            "service": service.name,
        }
    else:
        d["build"] = (challenge_path / service.path).as_posix()

    if service.extras is not None:
        d.update(service.extras)

    if service.__pydantic_extra__ is not None:
        d.update(service.__pydantic_extra__)

    if "restart" not in d:
        d["restart"] = "always"

    return d


def create_compose_file() -> None:
    """
    Creates a docker compose file for all challenges
    """

    try:
        port_mapping = load_port_mapping()
    except FileNotFoundError:
        raise ValueError("Port mappings not found, please generate them first")

    services = {}
    networks = {}

    for challenge in walk_challenges():
        if challenge.services is not None:
            network_name = challenge_name_to_network_name(challenge.name)

            if network_name not in networks:
                networks[network_name] = {}

            for service in challenge.services:
                if service.port is None:
                    host_port = None
                elif service.name not in port_mapping.mapping:
                    raise ValueError(
                        f"Port mapping not found for service: {service.name}"
                    )
                else:
                    host_port = port_mapping.mapping[service.name].to_port

                services[service.name] = create_compose_dict(
                    service, challenge.full_path, network_name, host_port
                )

    with open("docker-compose.yml", "w") as f:
        safe_dump({"version": "3", "services": services, "networks": networks}, f)
