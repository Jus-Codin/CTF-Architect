"""Constants used throughout CTF Architect."""

from ctfa.version import CHALLENGE_SPEC_VERSION, CTF_CONFIG_SPEC_VERSION

# CLI CONSTANTS
APP_CMD_NAME = "ctfa"

# CONFIG FILE CONSTANTS
CHALLENGE_CONFIG_FILE = "chall.yaml"
CTF_CONFIG_FILE = "ctf_config.yaml"
CHALLENGE_CONFIG_HEADER = f"""\
Challenge Metadata File (version {CHALLENGE_SPEC_VERSION})
This file is machine generated. DO NOT EDIT unless you know what you are doing.
If you want to create or edit a challenge, use the CTF Architect CLI instead.
"""

CTF_CONFIG_HEADER = f"""\
CTF Repository Metadata File (version {CTF_CONFIG_SPEC_VERSION})
This file is machine generated. DO NOT EDIT unless you know what you are doing.
This is the file to specify to the CTF Architect CLI when creating a new challenge.
"""

# PORT MAPPING CONSTANTS
PORT_MAPPING_FILE = "port_mapping.yaml"

# WORKFLOWS CONSTANTS
WORKFLOWS_CONFIG_FILE = "ctf_workflows.yaml"
WORKFLOWS_CONFIG_HEADER = """\
CTF Workflows Metadata File
This file is user editable and may be updated by the CTF Architect CLI.
Workflow configuration is resolved relative to the repository root unless otherwise stated.
"""
