from __future__ import annotations

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
