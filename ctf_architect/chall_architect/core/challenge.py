from __future__ import annotations

import shutil
from pathlib import Path
from typing import overload
from warnings import warn

from tomlkit import comment, document, dump, nl

from ctf_architect.chall_architect.core.utils import copytree_non_endless
from ctf_architect.core.constants import (
    CHALLENGE_CONFIG_FILE,
    SPECIFICATION_VERSION_STRING,
)
from ctf_architect.core.models import Challenge, Flag, Hint, Service


def save_challenge_config(folder: Path, challenge: Challenge):
    doc = document()
    doc.add(
        comment(f"Challenge Metadata File (version {SPECIFICATION_VERSION_STRING})")
    )
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

    doc.add("version", SPECIFICATION_VERSION_STRING)

    doc.add("challenge", challenge.model_dump(mode="json", exclude_defaults=True))

    with open(folder / CHALLENGE_CONFIG_FILE, "w") as f:
        dump(doc, f)


def create_challenge(
    name: str,
    description: str,
    difficulty: str,
    category: str,
    author: str,
    folder_name: str | None = None,
    source_files: list[Path] | None = None,
    solution_files: list[Path] | None = None,
    files: list[Path | str] | None = None,
    requirements: list[str] | None = None,
    extras: dict[str, str] | None = None,
    flags: list[dict | Flag] | None = None,
    hints: list[dict | Hint] | None = None,
    services: list[dict | Service] | None = None,
) -> tuple[Challenge, Path]:
    challenge = Challenge(
        name=name,
        description=description,
        difficulty=difficulty,
        category=category,
        author=author,
        requirements=requirements,
        extras=extras,
    )

    if folder_name is not None:
        challenge.folder_name = folder_name

    if flags is not None:
        flags = [
            flag if isinstance(flag, Flag) else Flag.model_validate(flag)
            for flag in flags
        ]
        challenge.flags = flags

    if hints is not None:
        hints = [
            hint if isinstance(hint, Hint) else Hint.model_validate(hint)
            for hint in hints
        ]
        challenge.hints = hints

    create_dist = files is not None
    create_src = source_files is not None
    create_service = services is not None
    create_writeup_md = solution_files is None or "writeup.md" in [
        f.name for f in solution_files
    ]

    challenge_path = Path(challenge.folder_name)

    _files_to_copy: list[tuple[Path, Path]] = []  # (source, destination)
    _folders_to_copy: list[tuple[Path, Path]] = []  # (source, destination)

    _files: list[Path | str] | None = None

    if files is not None:
        # Copy files to dist folder, unless they are already in the dist folder
        _files = []
        for file in files:
            if isinstance(file, Path):
                # Check if file exists
                if not file.exists():
                    raise ValueError(f"File does not exist: {file}")

                if not file.is_file():
                    raise ValueError(f"File must be a file: {file}")

                # Check if the file is in the dist folder
                if file.parent.resolve() == challenge_path.resolve() / "dist":
                    _files.append(file.relative_to(challenge_path.resolve()))
                else:
                    _files_to_copy.append((file, challenge_path / "dist"))
                    _files.append((challenge_path / "dist").relative_to(challenge_path))
            else:
                # It is a URL
                _files.append(file)

        challenge.files = _files

    _services: list[dict] | None = None

    if services is not None:
        # Copy services to service folder, unless they are already in the service folder
        _services = []
        for service in services:
            if isinstance(service, Service):
                _service = service
            else:
                _service = Service.model_validate(service)

            # Check if service exists
            if not _service.path.exists():
                raise ValueError(f"Service does not exist: {_service.path}")

            if not _service.path.is_dir():
                raise ValueError(f"Service must be a folder: {_service.path}")

            # Check if service is already in correct folder
            if (
                _service.path.resolve()
                == challenge_path.resolve() / "service" / _service.path.name
            ):
                _service.path = _service.path.relative_to(challenge_path.resolve())
            else:
                _folders_to_copy.append(
                    (_service.path, challenge_path / "service" / _service.path.name)
                )
                _service.path = (
                    challenge_path / "service" / _service.path.name
                ).relative_to(challenge_path)

            _services.append(_service)

        challenge.services = _services

    if source_files is not None:
        for file in source_files:
            if not file.exists():
                raise ValueError(f"Source file does not exist: {file}")
            if not file.is_file():
                raise ValueError(f"Source file must be a file: {file}")
            if file.parent.resolve() != challenge_path.resolve() / "src":
                _files_to_copy.append((file, challenge_path / "src"))

    if solution_files is not None:
        for file in solution_files:
            if not file.exists():
                raise ValueError(f"Solution file does not exist: {file}")
            if not file.is_file():
                raise ValueError(f"Solution file must be a file: {file}")
            if file.parent.resolve() != challenge_path.resolve() / "solution":
                _files_to_copy.append((file, challenge_path / "solution"))

    challenge_path.mkdir(exist_ok=True)

    (challenge_path / CHALLENGE_CONFIG_FILE).touch()
    (challenge_path / "README.md").touch()

    if create_dist:
        (challenge_path / "dist").mkdir(exist_ok=True)

    if create_src:
        (challenge_path / "src").mkdir(exist_ok=True)

    if create_service:
        (challenge_path / "service").mkdir(exist_ok=True)

    (challenge_path / "solution").mkdir(exist_ok=True)

    if create_writeup_md:
        (challenge_path / "solution" / "writeup.md").touch()

    # Copy files and folders
    for source, destination in _files_to_copy:
        shutil.copy(source, destination)

    for source, destination in _folders_to_copy:
        if source.resolve() in destination.resolve().parents:
            warn(
                f'Source folder "{source}" contains destination folder "{destination}", files may not be copied correctly'
            )
        copytree_non_endless(source, destination)

    save_challenge_config(challenge_path, challenge)

    return challenge, challenge_path


@overload
def update_challenge(
    old_challenge: Challenge,
    *,
    name: str | None = None,
    description: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    author: str | None = None,
    folder_name: str | None = None,
    files: list[Path | str] | None = None,
    requirements: list[str] | None = None,
    extras: dict[str, str] | None = None,
    flags: list[dict | Flag] | None = None,
    hints: list[dict | Hint] | None = None,
    services: list[dict | Service] | None = None,
) -> None: ...


def update_challenge(
    old_challenge: Challenge,
    **kwargs: str | list[Path | str] | dict | Hint | Flag | Service,
) -> None:
    old_challenge = old_challenge.model_copy(deep=True)

    # WARNING: This function MUST be run in the challenge folder else unintended behavior may occur
    _cwd = Path.cwd()

    # Not a fullproof check, but should be good enough cause it shouldn't happen anyway
    if _cwd.name != old_challenge.folder_name:
        raise RuntimeError(
            f"Current working directory is not the challenge folder: {_cwd}"
        )

    if "flags" in kwargs:
        kwargs["flags"] = [
            flag if isinstance(flag, Flag) else Flag.model_validate(flag)
            for flag in kwargs["flags"]
        ]

    if "hints" in kwargs:
        kwargs["hints"] = [
            hint if isinstance(hint, Hint) else Hint.model_validate(hint)
            for hint in kwargs["hints"]
        ]

    create_dist = False
    create_service = False

    _files_to_remove: list[Path] = []
    _files_to_copy: list[tuple[Path, Path]] = []  # (source, destination)
    _folders_to_remove: list[Path] = []
    _folders_to_copy: list[tuple[Path, Path]] = []  # (source, destination)

    # File paths could potentially be outside the challenge folder if they are new
    # Additionally, it is possible that new file's name is the same as an existing file
    # First, we find what files are new and what files are removed
    # Then, we remove the files that are no longer needed and copy the new files
    if "files" in kwargs:
        _old_files = {f.resolve() for f in old_challenge.files or []}
        _new_files = {f.resolve() for f in kwargs["files"] or []}

        removed_files = _old_files - _new_files
        added_files = _new_files - _old_files

        _files = [f.relative_to(_cwd) for f in _old_files & _new_files]

        for file in removed_files:
            if isinstance(file, Path):
                # Check if the file is in the challenge dist folder
                if file.parent.resolve() == _cwd / "dist":
                    # This should never happen, but we never know
                    # Some user might've manually edited the challenge config
                    # Ideally the program should not delete files that are not in the challenge folder
                    # So we just warn the user and don't delete the file
                    warn(
                        f'File "{file}" is not in the challenge folder, skipping deletion'
                    )
                    continue

                # Check if the file exists
                if not file.exists():
                    warn(f'File "{file}" does not exist, skipping deletion')
                    continue

                if not file.is_file():
                    warn(f'File "{file}" is not a file, skipping deletion')
                    continue

                _files_to_remove.append(file)

        for file in added_files:
            if isinstance(file, Path):
                # Check if the file exists
                if not file.exists():
                    raise ValueError(f'File "{file}" does not exist')

                if not file.is_file():
                    raise ValueError(f'File "{file}" is not a file')

                # Check if the file is in the challenge dist folder
                if file.parent.resolve() == _cwd / "dist":
                    _files.append(file.relative_to(_cwd))

                # Check if there is a file with the same name in the challenge folder
                if (_cwd / "dist" / file.name).exists():
                    raise ValueError(
                        f'File with name "{file.name}" already exists in challenge folder'
                    )
                else:
                    _files_to_copy.append((file, _cwd / "dist"))
                    _files.append((_cwd / "dist").relative_to(_cwd))

        if added_files and not (_cwd / "dist").exists():
            create_dist = True

        kwargs["files"] = _files

    if "services" in kwargs:
        _old_services = old_challenge.services or []
        _new_services = kwargs["services"] or []

        _removed_services: list[Service] = []
        _added_services: list[Service] = []

        _services: list[Service] = []

        # Create hashmap of old service paths to service objects
        # Iterate over new services and check if their paths are in the hashmap
        # If they are, check if the service object is the same
        #   If it is, pop the service object from the hashmap
        #   If it is not, pop the old service object and add the new service object to the main list
        # If they are not, add the new service object to the added list
        # Remaining service objects in the hashmap are removed services
        _old_services_map = {s.path.resolve(): s for s in _old_services}

        for service in _new_services:
            if isinstance(service, Service):
                _service = service
            else:
                _service = Service.model_validate(service)

            if _service.path.resolve() in _old_services_map:
                _old_service = _old_services_map.pop(_service.path.resolve())
                if _service != _old_service:
                    _added_services.append(_service)
                else:
                    _services.append(_service)
            else:
                _added_services.append(_service)

        _removed_services = list(_old_services_map.values())

        for service in _removed_services:
            # Check if the service is in the challenge service folder
            if service.path.resolve() != _cwd / "service" / service.path.name:
                # This should never happen, but we never know
                # Some user might've manually edited the challenge config
                # Ideally the program should not delete files that are not in the challenge folder
                # So we just warn the user and don't delete the service
                warn(
                    f'Service "{service.path}" is not in the challenge service folder, skipping deletion'
                )
                continue

            # Check if the service exists
            if not service.path.exists():
                warn(f'Service "{service.path}" does not exist, skipping deletion')
                continue

            # Check if the service is a directory
            if not service.path.is_dir():
                warn(f'Service "{service.path}" is not a directory, skipping deletion')
                continue

            _folders_to_remove.append(service.path)

        for service in _added_services:
            # Check if the service exists
            if not service.path.exists():
                raise ValueError(f'Service "{service.path}" does not exist')

            # Check if the service is a directory
            if not service.path.is_dir():
                raise ValueError(f'Service "{service.path}" is not a directory')

            # Check if the service is already in the correct folder
            if service.path.resolve() == _cwd / "service" / service.path.name:
                service.path = service.path.relative_to(_cwd)

            # Check if there is a service with the same name in the challenge folder
            if (_cwd / "service" / service.path.name).exists():
                raise ValueError(
                    f'Service folder with name "{service.path.name}" already exists in challenge folder'
                )
            else:
                _folders_to_copy.append(
                    (service.path, _cwd / "service" / service.path.name)
                )
                service.path = (_cwd / "service" / service.path.name).relative_to(_cwd)

            _services.append(service)

        if _added_services and not (_cwd / "service").exists():
            create_service = True

        kwargs["services"] = _services

    new_challenge = old_challenge.model_copy(update=kwargs)

    if create_dist:
        (_cwd / "dist").mkdir(exist_ok=True)

    if create_service:
        (_cwd / "service").mkdir(exist_ok=True)

    # Remove files and folders
    for file in _files_to_remove:
        # User might have the file open, so give a warning when it errors out
        try:
            file.unlink(missing_ok=True)
        except Exception as e:
            warn(f'Error deleting file "{file}": {e}')

    for folder in _folders_to_remove:
        # User might have the folder open, so give a warning when it errors out
        try:
            shutil.rmtree(folder)
        except Exception as e:
            warn(f'Error deleting folder "{folder}": {e}')

    # Copy files and folders
    for source, destination in _files_to_copy:
        shutil.copy(source, destination)

    for source, destination in _folders_to_copy:
        if source.resolve() in destination.resolve().parents:
            warn(
                f'Source folder "{source}" contains destination folder "{destination}", files may not be copied correctly'
            )
        copytree_non_endless(source, destination)

    save_challenge_config(_cwd, new_challenge)

    # Check if the folder name has changed
    if new_challenge.folder_name != old_challenge.folder_name:
        # As we are currently in the challenge folder, we cannot rename it
        # So we just warn the user to rename the folder manually
        warn(
            f'Challenge folder name has changed from "{old_challenge.folder_name}" to "{new_challenge.folder_name}", please rename the folder manually'
        )
