from __future__ import annotations

from ctf_architect.core.config import load_config
from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.models import PortMappingDict


def generate_port_mappings() -> dict[str, PortMappingDict]:
  config = load_config()

  port = config.port

  mapping: dict[str, PortMappingDict] = {}

  for category in config.categories:
    for challenge in walk_challenges(category):
      if challenge.services is not None:
        for service in challenge.services:
          if service.name in mapping:
            raise ValueError(f"Duplicate service name: {service.name}")
          mapping[service.name] = {
            "from_port": service.port,
            "to_port": str(port)
          }
          port += 1
    # If there is at least 1 service, go to the next thousand
    if port % 1000:
      port += 1000 - (port % 1000)

  # Check if we exceeded the port range
  # I'm sure this won't happen but just in case
  if port > 65535:
    raise ValueError("Port range exceeded")

  return mapping