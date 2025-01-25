from __future__ import annotations

import re
import shutil
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


def valid_service_folder(path: str | Path) -> bool:
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


def copytree_non_endless(src: str | Path, dst: str | Path) -> None:
    """
    Copy the contents of a folder to another folder, without copying the destination folder into itself.

    Args:
      src (str | Path): The source folder.
      dst (str | Path): The destination folder.
    """

    def _ignore(src: str, names: str):
        return {name for name in names if (Path(src) / name).resolve() == dst.resolve()}

    shutil.copytree(src, dst, ignore=_ignore)


def valid_challenge_folder_name(name: str) -> bool:
    """
    Check if a given challenge name is a valid folder name.

    Args:
      name (str): The name to be checked.

    Returns:
      bool: True if the name is a valid folder name, False otherwise.
    """
    # Check if the name is empty
    if not name:
        return False

    # Check if the name starts or ends with a space
    if name[0] == " " or name[-1] == " ":
        return False

    # Check if the name contains only alphanumeric characters, spaces, and underscores
    return bool(re.match(r"^[a-zA-Z0-9_ ]+$", name))


def valid_service_name(name: str) -> bool:
    """
    Check if a given service name is valid.

    Args:
      name (str): The name to be checked.

    Returns:
      bool: True if the name is a valid folder name, False otherwise.
    """
    return bool(re.match(r"^[a-z0-9][a-z0-9_-]*$", name))


def init_gui() -> None:
    import os

    if os.name == "nt":
        try:
            import ctypes

            # Set the DPI awareness to make the file dialog not blurry on Windows
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    import tkinter as tk

    # Hide the root window
    _root = tk.Tk()
    _root.withdraw()

    _root.wm_attributes("-topmost", True)
