"""
Various utility functions for chall-architect
"""

from __future__ import annotations

from pathlib import Path

from yaml import safe_load

from ctf_architect.core.models import Config


def get_config(path: str | Path) -> Config:
  """
  Gets the config from a given path.
  """
  if isinstance(path, str):
    path = Path(path)

  # Ensure path is a file
  if not path.is_file():
    raise ValueError("Path must be a file")
  
  # Ensure path is a yaml file
  if path.suffix != ".yaml":
    raise ValueError("Path must be a yaml file")
  
  # Load the config
  with path.open("r") as f:
    data = safe_load(path.open("r"))

  config = data.get("config")

  # Ensure config is present
  if config is None:
    raise ValueError("Config not found in yaml file")
  
  config = Config(**config)

  return config


def is_valid_service_folder(path: str | Path) -> bool:
  """
  Checks if the given path is a valid service folder.

  A service folder is considered valid if it has a dockerfile.
  """
  if isinstance(path, str):
    path = Path(path)

  # Check if there is a docker file in the folder, case-insensitive
  return any(file.name.lower() == "dockerfile" for file in path.iterdir())