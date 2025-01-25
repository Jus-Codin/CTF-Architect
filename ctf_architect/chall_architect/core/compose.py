from __future__ import annotations

from pathlib import Path

import yaml

from ctf_architect.core.compose import sanitize_name
from ctf_architect.core.models import Challenge, Service


def create_compose_service(
    service: Service,
    challenge_name: str,
    network_name: str,
    compose_path: Path,
) -> dict:
    """Create a Compose Service from a challenge service

    Parameters
    ----------
    service : Service
        The challenge service
    challenge_name : str
        The name of the challenge that the service belongs to
    network_name : str
        The name of the network to add the service to

    Returns
    -------
    dict
        A dictionary representation of the Compose Service
    """

    compose_service = {
        "container_name": sanitize_name(f"{challenge_name}-{service.name}"),
        "networks": [network_name],
        "build": (service.path.relative_to(compose_path)).as_posix(),
        "restart": "always",
    }

    ports = []

    for port in service.ports_list:
        if service.type == "internal":
            ports.append(f"{port}")
        else:
            ports.append(f"{port}:{port}")

    if ports:
        compose_service["ports"] = ports

    extras = service.extras if service.extras is not None else {}

    for key in extras:
        if key == "restart" or key not in compose_service:
            compose_service[key] = extras[key]

    return compose_service


def create_challenge_compose_dict(
    compose_path: Path, challenge_name: str, services: list[Service]
) -> dict:
    """Create a Compose dictionary for a challenge

    Parameters
    ----------
    challenge : Challenge
        The challenge to create a Compose dictionary for
    """

    network_name = f"{sanitize_name(challenge_name)}-network"

    _services = {}

    for service in services:
        _services[service.name] = create_compose_service(
            service, challenge_name, network_name, compose_path
        )

    return {"networks": {network_name: {"driver": "bridge"}}, "services": _services}


def create_challenge_compose_file(challenge: Challenge):
    """Create a Compose file for a challenge

    Parameters
    ----------
    challenge : Challenge
        The challenge to create a Compose file for
    """

    compose_path = Path(challenge.folder_name) / "service" / "compose.yml"

    with open(compose_path, "w") as f:
        yaml.safe_dump(
            create_challenge_compose_dict(
                compose_path, challenge.name, challenge.services
            ),
            f,
        )
