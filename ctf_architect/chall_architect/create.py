from __future__ import annotations

import re
import shutil
from pathlib import Path

from tomlkit import comment, document, dump, nl

from ctf_architect.core.challenge import create_challenge_readme
from ctf_architect.core.constants import CHALLENGE_CONFIG_FILE, SPECIFICATION_VERSION
from ctf_architect.core.models import Challenge, Flag, Hint, Service


def create_challenge_folder(
    name: str, dist: bool = False, service: bool = False
) -> Path:
    challenge_path = Path(name)
    challenge_path.mkdir(exist_ok=True)

    if dist:
        (challenge_path / "dist").mkdir(exist_ok=True)

    if service:
        (challenge_path / "service").mkdir(exist_ok=True)

    (challenge_path / "solution").mkdir(exist_ok=True)

    # Create empty files
    (challenge_path / CHALLENGE_CONFIG_FILE).touch()
    (challenge_path / "README.md").touch()

    return challenge_path


def create_challenge(
    name: str,
    description: str,
    difficulty: str,
    category: str,
    author: str,
    solution_files: list[Path],
    flags: list[dict[str, str | bool]],
    extras: dict | None = None,
    hints: list[dict[str, str | int]] | None = None,
    files: list[Path] | None = None,
    requirements: list[str] | None = None,
    services: list[dict] | None = None,
    docker_compose: Path | None = None,
) -> Path:
    flags = [Flag.model_validate(flag) for flag in flags]

    if hints is not None:
        hints = [Hint.model_validate(hint) for hint in hints]

    dist = files is not None
    service = services is not None

    folder_name = re.sub(r"[^a-zA-Z0-9-_ ]", "", name).strip()

    path = create_challenge_folder(folder_name, dist, service)

    if files is not None:
        # Copy files to dist folder, unless they are already in the dist folder
        file_paths = []
        for file in files:
            if isinstance(file, Path):
                if file.parent.resolve() != path.resolve() / "dist":
                    file_path = shutil.copy(file, path / "dist")
                    file_path = Path(file_path).relative_to(path)
                    file_paths.append(file_path)
                else:
                    file_path = file.relative_to(path.resolve())
                    file_paths.append(file_path)
            else:
                # It is a URL
                file_paths.append(file)
    else:
        file_paths = None

    if services is not None:
        # Copy services to service folder, unless they are already in the service folder
        _services = []
        for service in services:
            _service = Service.model_validate(service)
            service_path = _service.path

            if not service_path.is_dir():
                raise ValueError(f"Service path must be a directory: {service_path}")

            if service_path.resolve() != path.resolve() / "service" / service_path.name:
                service_path = shutil.copytree(
                    service_path,
                    path / "service" / service_path.name,
                    dirs_exist_ok=True,
                )
                service_path = Path(service_path).relative_to(path)
            else:
                service_path = service_path.relative_to(path.resolve())
            _service.path = service_path
            _services.append(_service)

        services = _services
    else:
        services = None

    if docker_compose is not None:
        if not docker_compose.name == "docker-compose.yml":
            raise ValueError("Docker compose file must be named 'docker-compose.yml'")
        if docker_compose.parent.resolve() != path.resolve() / "service":
            shutil.copy(docker_compose, path / "service")

    # Copy solution files to solution folder, unless they are already in the solution folder
    for file in solution_files:
        if file.parent.resolve() != path.resolve() / "solution":
            shutil.copy(file, path / "solution")

    challenge = Challenge(
        name=name,
        description=description,
        difficulty=difficulty,
        category=category,
        author=author,
        flags=flags,
        extras=extras,
        hints=hints,
        files=file_paths,
        requirements=requirements,
        services=services,
    )

    # Write challenge config file
    doc = document()
    doc.add(comment(f"Challenge Metadata File (version {SPECIFICATION_VERSION})"))
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

    with open(path / CHALLENGE_CONFIG_FILE, "w") as f:
        dump(doc, f)

    # Write README
    with open(path / "README.md", "w", encoding="utf-8") as f:
        f.write(create_challenge_readme(challenge))

    return path
