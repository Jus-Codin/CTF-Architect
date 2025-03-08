"""Constants used throughout CTF Architect."""

from ctf_architect.version import CHALLENGE_SPEC_VERSION, CTF_CONFIG_SPEC_VERSION

# CLI CONSTANTS
APP_CMD_NAME = "ctfa"
APP_CONFIG_FILE = "app_config.toml"

# CONFIG FILE CONSTANTS
CHALLENGE_CONFIG_FILE = "chall.toml"
CTF_CONFIG_FILE = "ctf_config.toml"

CHALLENGE_CONFIG_HEADER = f"""\
Challenge Metadata File (version {CHALLENGE_SPEC_VERSION})
This file is machine generated. DO NOT EDIT unless you know what you are doing.
If you want to create or edit a challenge, use the CLI instead.
"""

CTF_CONFIG_HEADER = f"""\
CTF Repository Metadata File (version {CTF_CONFIG_SPEC_VERSION})
This file is machine generated. DO NOT EDIT unless you know what you are doing.
This is the file to specify to ctf-architect when creating a new challenge.
"""

# PORT MAPPING CONSTANTS
PORT_MAPPING_FILE = "port_mapping.yaml"

# README FILE TEMPLATES
CHALL_README_TEMPLATE = """\
# {name}
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

CATEGORY_README_TEMPLATE = """\
# {name} Challenges

## Difficulty Distribution
| Difficulty | Number of Challenges |
|------------|:--------------------:|
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

MAX_NAME_LENGTH = 30
MAX_DESCRIPTION_LENGTH = 50
