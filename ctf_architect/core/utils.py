from __future__ import annotations

import re

from ctf_architect.core.constants import SPECIFICATION_VERSION


def is_supported_specification_version(version: str) -> bool:
    """
    Check if the specified version is supported by the current version of CTF Architect.
    """

    segments = version.split(".")

    if len(segments) != 2:
        return False
    else:
        major, minor = segments

    return (
        int(major) == SPECIFICATION_VERSION.MAJOR
        and int(minor) <= SPECIFICATION_VERSION.MINOR
    )


def sanitize_challenge_name(name: str) -> str:
    """
    Sanitize a challenge name to be used as a folder name.
    """

    return re.sub(r"[^a-zA-Z0-9-_ ]", "", name).strip()
