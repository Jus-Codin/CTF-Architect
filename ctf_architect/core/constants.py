# CLI CONSTANTS
APP_CMD_NAME = "ctf-architect"

# CONFIG FILE CONSTANTS
CTF_CONFIG_FILE = "ctf_config.toml"
CHALLENGE_CONFIG_FILE = "chall.toml"
SPECIFICATION_VERSION = "0.1"

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
This directory contains challenges related to {name}.

## Difficulty Distribution
| Difficulty | Number of Challenges |
| ---------- |:--------------------:|
{diff_table}

## Challenges ({count} total)
| Name | Description | Difficulty | Author |
| ---- | ----------- | ---------- | ------ |
{challenges_table}
"""

ROOT_README_TEMPLATE = """# Challenges
This directory contains all challenges.

## Difficulty Distribution
{diff_table}

## Challenges ({count} total)
| Name | Description | Category | Difficulty | Author |
| ---- | ----------- | -------- | ---------- | ------ |
{challenges_table}
"""
