from __future__ import annotations

from typing import NamedTuple


class Version(NamedTuple):
    MAJOR: int
    MINOR: int

    def __str__(self):
        return f"{self.MAJOR}.{self.MINOR}"


# VERSIONING CONSTANTS
CHALLENGE_SPEC_VERSION = Version(MAJOR=0, MINOR=1)
CTF_CONFIG_SPEC_VERSION = Version(MAJOR=0, MINOR=1)
PORT_MAPPING_SPEC_VERSION = Version(MAJOR=0, MINOR=1)


def is_supported_challenge_version(version: str) -> bool:
    """Check if the specified challenge version is supported by the current version of CTF Architect."""
    segments = version.split(".")

    # In the future we may want to support more than just major and minor versions
    # so we check for exactly 2 segments
    if len(segments) != 2:
        return False
    else:
        major, minor = segments

    # In the future there may be a CTF Config version that is incompatible with
    # previous challenge versions, so we may want to check the CTF Config version here in the future
    return int(major) == CHALLENGE_SPEC_VERSION.MAJOR and int(minor) <= CHALLENGE_SPEC_VERSION.MINOR


def is_supported_ctf_config_version(version: str) -> bool:
    """Check if the specified CTF Config version is supported by the current version of CTF Architect."""
    segments = version.split(".")

    # In the future we may want to support more than just major and minor versions
    # so we check for exactly 2 segments
    if len(segments) != 2:
        return False
    else:
        major, minor = segments

    return int(major) == CTF_CONFIG_SPEC_VERSION.MAJOR and int(minor) <= CTF_CONFIG_SPEC_VERSION.MINOR
