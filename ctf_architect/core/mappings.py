from __future__ import annotations

from ctf_architect.core.config import load_config
from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.models import PortMappingDict


def generate_port_mappings() -> dict[str, PortMappingDict]:
  config = load_config()

  port = config.port

  mapping: dict[str, PortMappingDict] = {}

  for challenge in walk_challenges():
    if challenge.services is not None:
      for service in challenge.services:
        if service.name in mapping:
          raise ValueError(f"Duplicate service name: {service.name}")
        mapping[service.name] = {
          "from_port": service.port,
          "to_port": str(port)
        }
        port += 1

  return mapping