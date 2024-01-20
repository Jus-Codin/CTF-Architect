"""
Functionality for creating a docker compose file
"""

from __future__ import annotations

from pathlib import Path
from yaml import safe_dump

from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.config import load_config
from ctf_architect.core.models import Service


def challenge_name_to_network_name(challenge_name: str) -> str:
  """
  Converts a challenge name to a network name

  All non alphanumeric characters are removed, and spaces are replaced with dashes
  """
  return "".join(
    c for c in challenge_name.lower().replace(" ", "-")
    if c.isalnum()
  )


def create_compose_dict(
    service: Service,
    challenge_name: str,
    network_name: str,
    category: str,
    host_port: str
  ) -> dict:
  """
  Creates a docker compose service for a challenge service
  """
  
  service_path = (
    Path("./challenges") / category /
    challenge_name / service.path
  ).as_posix()

  d = {
      "build": service_path,
      "ports": [f"{host_port}:{service.port}"],
      "container_name": service.name,
      "networks": [network_name]
  }

  if service.extras is not None:
    d.update(service.extras)

  if "restart" not in d:
    d["restart"] = "always"

  return d


def create_compose_file() -> None:
  """
  Creates a docker compose file for all challenges
  """

  config = load_config()

  if config.port_mappings is None:
    raise ValueError("Port mappings not found in config, please generate them first")

  services = {}
  networks = {}

  for challenge in walk_challenges():
    if challenge.services is not None:

      network_name = challenge_name_to_network_name(challenge.name)

      if network_name not in networks:
        networks[network_name] = {
          "internal": True,
          "name": network_name
        }

      for service in challenge.services:
        services[service.name] = create_compose_dict(
          service,
          challenge.name,
          network_name,
          challenge.category.lower(),
          config.port_mappings[service.name]["to_port"]
        )

  with open("docker-compose.yml", "w") as f:
    safe_dump({
      "version": "3",
      "services": services,
      "networks": networks
    }, f)