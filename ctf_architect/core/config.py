import os
from functools import lru_cache

from pydantic import ValidationError
from tomlkit import comment, document, dump, load, nl

from ctf_architect.core.constants import CTF_CONFIG_FILE, SPECIFICATION_VERSION_STRING
from ctf_architect.core.models import ConfigFile, CTFConfig


@lru_cache
def load_config() -> CTFConfig:
    if not os.path.exists(CTF_CONFIG_FILE):
        raise FileNotFoundError(f"Could not find {CTF_CONFIG_FILE}")

    with open(CTF_CONFIG_FILE, "r") as f:
        data = load(f)

    try:
        config_file = ConfigFile.model_validate(data.unwrap())
    except ValidationError as e:
        raise ValueError(f"Error loading CTF config file: {e}")

    return config_file.config


def save_config(config: CTFConfig) -> None:
    doc = document()
    doc.add(comment(f"CTF Repo Config File (version {SPECIFICATION_VERSION_STRING})"))
    doc.add(
        comment(
            "This file is machine generated. DO NOT EDIT unless you know what you are doing."
        )
    )
    doc.add(
        comment(
            "This is the file to specify to chall-architect when creating a new challenge"
        )
    )
    doc.add(nl())

    doc.add("version", SPECIFICATION_VERSION_STRING)
    doc.add("config", config.model_dump(mode="json", exclude_defaults=True))

    with open(CTF_CONFIG_FILE, "w") as f:
        dump(doc, f)
