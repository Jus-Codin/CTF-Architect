from __future__ import annotations

import os
from functools import lru_cache

import yaml

from ctf_architect.constants import PORT_MAPPING_FILE
from ctf_architect.core.exceptions import (
    DuplicateServiceNameError,
    MissingStartingPortError,
)
from ctf_architect.core.repo import load_repo_config, walk_challenges
from ctf_architect.models.port_mapping import PortMapping, PortMappingFile


@lru_cache
def load_port_mapping() -> dict[str, list[PortMapping]]:
    """Load the port mapping from the port_mapping.yaml file.

    Returns:
        dict[str, list[PortMapping]]: A dictionary of service names to port mappings.

    Raises:
        FileNotFoundError: If the port_mapping.yaml file is not found.
    """
    if not os.path.exists(PORT_MAPPING_FILE):
        raise FileNotFoundError(f"Could not find {PORT_MAPPING_FILE}")

    with open(PORT_MAPPING_FILE) as f:
        data = yaml.safe_load(f)

    mapping_file = PortMappingFile.model_validate(data)

    return mapping_file.mapping


def save_port_mapping(mapping: dict[str, list[PortMapping]]) -> None:
    """Save the port mapping to the port_mapping.yaml file."""
    data = PortMappingFile.from_mapping(mapping)

    with open(PORT_MAPPING_FILE, "w") as f:
        yaml.safe_dump(data.model_dump(), f)


def generate_port_mapping(seperation: int | None = 1000, max_port: int = 65535) -> dict[str, list[PortMapping]]:
    """Generate a port mapping for services in the repository.

    Args:
        seperation (int | None, optional): The number of ports to separate public services by. Defaults to 1000.
        max_port (int, optional): The maximum port number to use. Defaults to 65535.

    Returns:
        dict[str, list[PortMapping]]: A dictionary of service names to port mappings.

    Raises:
        DuplicateServiceNameError: If there are multiple services with the same name.
        MissingStartingPortError: If no starting port is specified in the repo config.
        ValueError: If the starting port is greater than the max port or there are not enough ports to assign to all services.
    """
    config = load_repo_config()

    if config.starting_port is None:
        raise MissingStartingPortError("No starting port specified in the repo config")

    port = config.starting_port

    if port > max_port:
        raise ValueError("Starting port is greater than max port")

    mapping = {}
    # secret_services = []

    # There has to be a better way to do this...
    for category in config.categories:
        for challenge in walk_challenges(category):
            if challenge.services is not None:
                for service in challenge.services:
                    service_name = service.unique_name(challenge)

                    if service_name in mapping:
                        raise DuplicateServiceNameError(f"Duplicate service name: {service_name}")

                    service_mapping = []

                    for service_port in service.ports_list:
                        # TODO: Create built-in solution for randomised ports for secret services
                        # if service.type == "secret":
                        #     secret_services.append((service_name, service))
                        if service.type == "internal":
                            service_mapping.append(PortMapping(from_port=service_port, to_port=None))
                        else:
                            service_mapping.append(PortMapping(from_port=service_port, to_port=port))
                            port += 1

                    mapping[service_name] = service_mapping

        if seperation is not None:
            # If there is at least one public service, add a separation between them
            if port % seperation:
                port += seperation - (port % seperation)

    if port > max_port:
        raise ValueError("Not enough ports to assign to all services")

    return mapping
