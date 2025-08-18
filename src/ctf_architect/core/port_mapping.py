from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ctf_architect.constants import PORT_MAPPING_FILE
from ctf_architect.core.exceptions import (
    DuplicateServiceNameError,
    MissingStartingPortError,
)
from ctf_architect.core.repo import Repo
from ctf_architect.models.port_mapping import PortMapping, PortMappingFile

PortMappingsDict = dict[str, list[PortMapping]]


# TODO: Make the path variable mandatory to be specified to the function
@lru_cache
def load_port_mapping(path: str | Path = Path.cwd()) -> dict[str, list[PortMapping]]:
    """Load the port mapping from the port_mapping.yaml file.

    If the path is a directory, it will look for the port_mapping.yaml file in that directory.
    If the path is a file, it will load the port mapping from that file.

    Args:
        path (str | Path): The path to the port mapping file or directory. Defaults to the current working directory.

    Returns:
        dict[str, list[PortMapping]]: A dictionary of service names to port mappings.
    """
    if isinstance(path, str):
        path = Path(path)

    if path.is_file():
        fp = path
    else:
        fp = path / PORT_MAPPING_FILE

    with open(fp) as f:
        data = yaml.safe_load(f)

    mapping_file = PortMappingFile.model_validate(data)

    return mapping_file.mapping


def save_port_mapping(mapping: PortMappingsDict) -> None:
    """Save the port mapping to the port_mapping.yaml file.

    Args:
        mapping (dict[str, list[PortMapping]]): A dictionary of service names to port mappings.
    """
    data = PortMappingFile.from_mapping(mapping)

    with open(PORT_MAPPING_FILE, "w") as f:
        yaml.safe_dump(data.model_dump(), f)


def generate_port_mapping(
    repo_path: str | Path = Path.cwd(), seperation: int | None = 1000, max_port: int = 65535
) -> PortMappingsDict:
    """Generate a port mapping for services in the repository.

    Args:
        repo_path (str | Path): The path to the repository. Defaults to the current working directory.
        seperation (int | None, optional): The number of ports to separate public services by. Defaults to 1000.
        max_port (int, optional): The maximum port number to use. Defaults to 65535.

    Returns:
        PortMappingsDict: A dictionary of service names to port mappings.

    Raises:
        DuplicateServiceNameError: If there are multiple services with the same name.
        MissingStartingPortError: If no starting port is specified in the repo config.
        ValueError: If the starting port is greater than the max port or there are not enough ports to assign to all services.
    """
    repo = Repo.from_path(repo_path)

    if repo.ctf_config.starting_port is None:
        raise MissingStartingPortError("No starting port specified in the repo config")

    port = repo.ctf_config.starting_port

    if port > max_port:
        raise ValueError("Starting port is greater than max port")

    mapping = {}
    # secret_services = []

    for challenge in repo.walk_challenges():
        if challenge.config.services is not None:
            for service in challenge.config.services:
                service_name = service.unique_name(challenge.config)

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
