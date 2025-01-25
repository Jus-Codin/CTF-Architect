from __future__ import annotations

import re

from ctf_architect.cli.ui.prompts import InvalidResponse


def no_empty_string(response: str) -> None:
    if len(response) == 0:
        raise InvalidResponse("[ctfa.prompt.error]Please enter a value")


def valid_port(port: int) -> None:
    if port < 1 or port > 65535:
        raise InvalidResponse("[ctfa.prompt.error]Please enter a valid port number")


def valid_chall_folder_name(folder_name: str) -> None:
    if folder_name and not re.match(r"^[a-zA-Z][a-zA-Z0-9 _-]*$", folder_name):
        raise InvalidResponse(
            "[ctfa.prompt.error]Invalid challenge folder name. Folder name must start with a letter and contain only letters, numbers, spaces, underscores and hyphens."
        )


def valid_service_name(service_name: str) -> None:
    if not re.match(r"^[a-z][a-z0-9_-]*$", service_name):
        raise InvalidResponse(
            "[ctfa.prompt.error]Invalid service name. Service name must start with a lowercase letter and contain only lowercase letters, numbers, underscores and hyphens."
        )
