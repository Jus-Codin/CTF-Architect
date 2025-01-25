from pathlib import Path
from typing import Literal

from ctf_architect.core.models import Service


def create_new_service(
    name: str,
    type: Literal["web", "nc", "ssh", "secret", "internal"],
    path: Path | None = None,
    port: int | None = None,
    ports: list[int] | None = None,
) -> Service:
    if path is None:
        # NOTE: Make sure this get run in the challenge directory
        # Try to specify the path using the name
        service_path = Path(f"./service/{name}")
    else:
        # It's fine if the path is not in the services directory, as it will get copied to the services directory
        service_path = path

    service = Service(name=name, path=service_path, port=port, ports=ports, type=type)

    # Create path if it doesn't exist
    service.path.mkdir(parents=True, exist_ok=True)

    # Create Dockerfile in the service directory if it doesn't exist
    (service.path / "Dockerfile").touch(exist_ok=True)

    return service
