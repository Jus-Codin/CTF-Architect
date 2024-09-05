from typing import NamedTuple

# CLI CONSTANTS
APP_CMD_NAME = "ctf-architect"

# CONFIG FILE CONSTANTS
CTF_CONFIG_FILE = "ctf_config.toml"
CHALLENGE_CONFIG_FILE = "chall.toml"


# VERSIONING CONSTANTS
class Version(NamedTuple):
    MAJOR: int
    MINOR: int


SPECIFICATION_VERSION = Version(MAJOR=0, MINOR=1)
SPECIFICATION_VERSION_STRING = (
    f"{SPECIFICATION_VERSION.MAJOR}.{SPECIFICATION_VERSION.MINOR}"
)

# PORT MAPPING CONSTANTS
PORT_MAPPING_FILE = "port_mapping.json"

# STATS FILE TEMPLATES
CHALL_README_TEMPLATE = """# {name}
{description}

## Summary
- **Author:** {author}
- **Category:** {category}
- **Difficulty:** {difficulty}
{extras}

## Hints
{hints}

## Files
{files}

## Flags
{flags}

## Services
{services}
"""

CATEGORY_README_TEMPLATE = """# {name} Challenges

## Difficulty Distribution
| Difficulty | Number of Challenges |
| ---------- |:--------------------:|
{diff_table}

## Challenges ({count} total)
{challenges_table}

## Services ({service_count} total)
{services_table}
"""

ROOT_README_TEMPLATE = """# Challenges

## Difficulty Distribution
{diff_table}

## Challenges ({count} total)
{challenges_table}

## Services ({service_count} total)
{services_table}
"""
