from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError
from tomlkit import load

from ctf_architect.core.constants import CTF_CONFIG_FILE
from ctf_architect.core.models import ConfigFile, CTFConfig


@lru_cache
def load_config_from_path(path: Path | str) -> CTFConfig:
    if isinstance(path, str):
        path = Path(path)

    if not path.is_file():
        raise ValueError("Path must be a file")
    elif path.name != CTF_CONFIG_FILE:
        raise ValueError(f"Path name must be {CTF_CONFIG_FILE}")

    with path.open("r", encoding="utf-8") as f:
        data = load(f)

    try:
        config_file = ConfigFile.model_validate(data.value)
    except ValidationError as e:
        raise ValueError(f"Error loading CTF config file: {e}")

    return config_file.config
