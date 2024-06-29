from __future__ import annotations

import json
import os
from random import SystemRandom

from pydantic import ValidationError

from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.config import load_config
from ctf_architect.core.constants import CTF_CONFIG_FILE, PORT_MAPPING_FILE
from ctf_architect.core.models import PortMappingFile, ServicePortMapping


def load_port_mapping() -> PortMappingFile:
    """
    Load the port mapping from the port_mapping.json file.
    """
    if not os.path.exists(PORT_MAPPING_FILE):
        raise FileNotFoundError(f"Could not find {PORT_MAPPING_FILE}")

    with open(PORT_MAPPING_FILE, "r") as f:
        data = json.load(f)

    try:
        data = PortMappingFile(**data)
    except ValidationError as e:
        raise ValueError(f"Error loading port mapping file: {e}")

    return data


def save_port_mapping(mapping: dict[str, ServicePortMapping]) -> None:
    """
    Save the port mapping to the port_mapping.json file.
    """
    data = PortMappingFile.from_mapping(mapping)

    with open(PORT_MAPPING_FILE, "w") as f:
        json.dump(data.model_dump(), f)


def generate_port_mapping(
    seperation: int | None = 1000, max_port: int = 65535
) -> dict[str, ServicePortMapping]:
    config = load_config()

    port = config.starting_port

    if port > max_port:
        raise ValueError("Starting port is greater than max port")

    mapping = {}
    secret_services = []

    for category in config.categories:
        for challenge in walk_challenges(category):
            if challenge.services is not None:
                for service in challenge.services:
                    if service.type == "internal":
                        continue
                    elif service.name in mapping:
                        raise ValueError(f"Duplicate service name: {service.name}")
                    elif service.type == "secret":
                        secret_services.append(service)
                    else:
                        mapping[service.name] = ServicePortMapping(
                            from_port=service.port, to_port=port
                        )
                        port += 1

        if seperation is not None:
            # If there is at least 1 service in the category, go to the next seperation
            if port % seperation:
                port += seperation - (port % seperation)

    # Check if we exceeded the port range
    if port > max_port:
        raise ValueError("Port range exceeded")

    # Add the secret services
    # We want to make the secret services hard to find, so we randomly assign them to ports
    if secret_services:
        # Check if we have enough ports for the secret services
        if port + len(secret_services) > max_port:
            raise ValueError("Port range exceeded")

        ports = SystemRandom().sample(range(port, max_port + 1), len(secret_services))

        for service, port in zip(secret_services, ports):
            mapping[service.name] = ServicePortMapping(
                from_port=service.port, to_port=port
            )

    return mapping
