from __future__ import annotations

import re
import shutil
from pathlib import Path

from tomlkit import comment, document, dump, nl

from ctf_architect.core.challenge import create_challenge_readme, get_chall_config
from ctf_architect.core.constants import CHALLENGE_CONFIG_FILE, SPECIFICATION_VERSION
from ctf_architect.core.models import Challenge, Flag, Hint, Service


def edit_challenge(
    challenge_path: Path,
    name: str = None,
    description: str = None,
    difficulty: str = None,
    category: str = None,
    author: str = None,
    solution_files: list[Path] = None,
    flags: list[dict[str, str | bool]] = None,
    extras: dict = None,
    hints: list[dict[str, str | int]] = None,
    files: list[Path | str] = None,
    requirements: list[str] = None,
    services: list[dict] = None,
    docker_compose: Path | None = None,
) -> Path:
    """Edit a challenge by comparing the old configuration with the new one and updating the challenge folder."""

    old_challenge = get_chall_config(challenge_path)

    name = name or old_challenge.name
    description = description or old_challenge.description
    difficulty = difficulty or old_challenge.difficulty
    category = category or old_challenge.category
    author = author or old_challenge.author

    if flags is None:
        flags = old_challenge.flags
    elif len(flags) == 0:
        raise ValueError("At least one flag is required.")
    else:
        flags = [Flag.model_validate(flag) for flag in flags]

    if extras is None:
        extras = old_challenge.extras
    elif extras == {}:
        extras = None

    if hints is None:
        hints = old_challenge.hints
    elif len(hints) == 0:
        hints = None
    else:
        hints = [Hint.model_validate(hint) for hint in hints]

    if requirements is None:
        requirements = old_challenge.requirements
    elif len(requirements) == 0:
        requirements = None

    # NOTE: We do not know what solution files already exist, so we will not delete them
    for file in solution_files or []:
        if file.parent.resolve() != challenge_path.resolve() / "solution":
            shutil.copy(file, challenge_path / "solution")

    if files is None:
        files = old_challenge.files
    elif len(files) == 0:
        files = None
    else:
        # Find all the files that are in the dist folder but not in the new files list
        for file in old_challenge.files:
            if isinstance(file, Path) and file not in files:
                file.unlink()

        # Find all the files that are not in the dist folder
        _files = []
        for file in files:
            if isinstance(file, Path):
                if file.parent.resolve() != challenge_path.resolve() / "dist":
                    file = shutil.copy(file, challenge_path / "dist")
                    file = Path(file).relative_to(challenge_path)

                _files.append(file)
            else:
                _files.append(file)

        files = _files

    if services is None:
        services = old_challenge.services
    elif len(services) == 0:
        services = None
    else:
        # Find all the services that are in the service folder but not in the new services list
        for service in old_challenge.services:
            if service not in services:
                shutil.rmtree(challenge_path / "service" / service.path.name)

        # Copy services to service folder, unless they are already in the service folder
        _services = []
        for service in services:
            _service = Service.model_validate(service)
            service_path = _service.path

            if not service_path.is_dir():
                raise ValueError(f"Service path must be a directory: {service_path}")

            if (
                service_path.parent.resolve()
                != challenge_path.resolve() / "service" / service_path.name
            ):
                service_path = shutil.copytree(
                    service_path, challenge_path / "service" / service_path.name
                )
                service_path = Path(service_path).relative_to(challenge_path)
                _service.path = service_path
                _services.append(_service)
            else:
                _services.append(_service)

        services = _services

    if docker_compose is not None:
        if not docker_compose.name == "docker-compose.yml":
            raise ValueError("Docker compose file must be named 'docker-compose.yml'")
        if docker_compose.parent.resolve() != challenge_path.resolve() / "service":
            # Delete the old docker-compose.yml file if it exists
            if (challenge_path / "service" / "docker-compose.yml").exists():
                (challenge_path / "service" / "docker-compose.yml").unlink()
            shutil.copy(docker_compose, challenge_path / "service")

    # Write the new configuration to the challenge folder
    challenge = Challenge(
        name=name,
        description=description,
        difficulty=difficulty,
        category=category,
        author=author,
        flags=flags,
        extras=extras,
        hints=hints,
        files=files,
        requirements=requirements,
        services=services,
    )

    doc = document()
    doc.add(comment(f"CTF Repo Config File (version {SPECIFICATION_VERSION})"))
    doc.add(
        comment(
            "This file is machine generated. DO NOT EDIT unless you know what you are doing."
        )
    )
    doc.add(
        comment(
            "If you want to create or edit a challenge, use chall-architect instead."
        )
    )
    doc.add(nl())

    doc.add("version", SPECIFICATION_VERSION)

    doc.add("challenge", challenge.model_dump(mode="json", exclude_defaults=True))

    with open(challenge_path / CHALLENGE_CONFIG_FILE, "w") as f:
        dump(doc, f)

    # Write README
    with open(challenge_path / "README.md", "w", encoding="utf-8") as f:
        f.write(create_challenge_readme(challenge))

    return challenge_path
