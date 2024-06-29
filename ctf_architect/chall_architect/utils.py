from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError
from tomlkit import load

from ctf_architect.core.models import ConfigFile, CTFConfig


def get_config(path: str | Path) -> CTFConfig:
    """
    Load and validate a CTF config file.

    Args:
      path (str | Path): The path to the CTF config file.

    Returns:
      CTFConfig: The validated CTF config object.

    Raises:
      ValueError: If the path is not a file or if there is an error loading the config file.
    """
    if isinstance(path, str):
        path = Path(path)

    if not path.is_file():
        raise ValueError("Path must be a file")

    with path.open("r", encoding="utf-8") as f:
        data = load(f)

    try:
        config_file = ConfigFile.model_validate(data.value)
    except ValidationError as e:
        raise ValueError(f"Error loading CTF config file: {e}")

    return config_file.config


def is_valid_service_folder(path: str | Path) -> bool:
    """
    Check if a given folder contains a valid service.

    Args:
      path (str | Path): The path to the folder to be checked.

    Returns:
      bool: True if the folder contains a valid service, False otherwise.
    """
    if isinstance(path, str):
        path = Path(path)

    # Check if there is a docker file in the folder, case-insensitive
    return any(file.name.lower() == "dockerfile" for file in path.iterdir())
