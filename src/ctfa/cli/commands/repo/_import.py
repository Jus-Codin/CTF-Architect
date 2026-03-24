from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from cyclopts.types import ResolvedExistingPath

from ctfa.cli.param_types import ResolvedExistingChallengeRepository


def command(
    location: Annotated[ResolvedExistingPath, Parameter(name=["--location", "-l"])] = Path.cwd(),
    *,
    repository_path: Annotated[
        ResolvedExistingChallengeRepository, Parameter(name=["--repository", "-R"])
    ] = Path.cwd(),
    import_all: Annotated[bool, Parameter(name=["--all", "-a"], negative="")] = False,
    replace_existing: Annotated[bool, Parameter(name=["--replace", "-r"], negative="")] = False,
    no_update_stats: Annotated[bool, Parameter(name=["--no-update-stats", "-n"], negative="")] = False,
):
    """Import zipped collections of challenge folders into a challenge repository.

    Args:
        location (ResolvedExistingPath, optional): The path to the zip file or directory containing zip files
        repository_path (ResolvedExistingChallengeRepository, optional): The path to the challenge repository
        import_all (bool, optional): Whether to import all zip files in the specified location
        replace_existing (bool, optional): Whether to replace existing challenges in the repository
        no_update_stats (bool, optional): Whether to skip updating challenge statistics after import
    """
    from collections import deque
    from tempfile import TemporaryDirectory
    from zipfile import ZipFile

    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.prompts import confirm, multi_select
    from ctfa.core.exceptions import (
        ChallengeExistsError,
        ConfigFileNotFoundError,
        FolderNameCollisionError,
        InvalidChallengeRepositoryError,
    )
    from ctfa.core.repository import ChallengeRepository
    from ctfa.utils import is_challenge_folder

    try:
        repo = ChallengeRepository.load_repository(repository_path)
    except (InvalidChallengeRepositoryError, ConfigFileNotFoundError):
        console.print(
            f"Could not find the Repository Config file at {repository_path}. Are you sure this is the right directory?",
            style="ctfa.error",
        )
        return

    if location.is_file():
        zip_files = [location]
    else:
        zip_files = list(location.glob("*.zip"))
        if not import_all:
            _file_names = [zf.name for zf in zip_files]
            _selected = multi_select("Select the zip files to import", _file_names, return_indices=True).ask()
            zip_files = [zip_files[i] for i in _selected]

    successful_imports = 0
    unzip_failed: list[Path] = []
    import_failed: list[str] = []

    with TemporaryDirectory(dir=repo.location, prefix="ctfa_import_") as temp_dir:
        temp_path = Path(temp_dir)

        for zip_file in zip_files:
            target_path = temp_path / zip_file.stem

            try:
                with ZipFile(zip_file, "r") as zf:
                    zf.extractall(target_path)
            except Exception as e:
                console.print(f"Failed to extract '{zip_file}': {e}", style="ctfa.error")
                console.print_exception()
                unzip_failed.append(zip_file)
                continue

            challenge_folders: list[Path] = []

            # Check if the extracted folder is a challenge folder
            if is_challenge_folder(target_path):
                challenge_folders.append(target_path)
            else:
                # Recursively search in the extracted folder for challenge folders
                # Also don't go deeper in a folder if it is a challenge folder
                _queue = deque([target_path])

                # BFS
                while _queue:
                    current_path = _queue.popleft()

                    if is_challenge_folder(current_path):
                        challenge_folders.append(current_path)
                    else:
                        for child in current_path.iterdir():
                            if child.is_dir():
                                _queue.append(child)

            if not challenge_folders:
                console.print(
                    f":warning: No challenge folders found in '{zip_file}'. Skipping...",
                    style="ctfa.warning",
                )
                continue

            for challenge_folder in challenge_folders:
                asked_allow_replace = replace_existing

                while True:
                    try:
                        repo.add_challenge(challenge_folder, replace_existing=asked_allow_replace)
                        console.print(
                            f":white_check_mark: Successfully imported challenge from '{challenge_folder.name}'",
                            style="ctfa.success",
                        )

                        successful_imports += 1
                        break
                    except ChallengeExistsError:
                        if not confirm(
                            f"A challenge with the same ID ({challenge_folder.name}) already exists in the repository. Do you want to replace it? (y/n): "
                        ).ask():
                            import_failed.append(challenge_folder.name)
                            break
                        asked_allow_replace = True
                    except FolderNameCollisionError:
                        console.print(
                            f"The folder name '{challenge_folder.name}' is already used by a different challenge. Please resolve the conflict and try again.",
                            style="ctfa.error",
                        )
                        import_failed.append(challenge_folder.name)
                        break
                    except Exception as e:
                        console.print(
                            f"An unexpected error occurred while importing challenge from '{challenge_folder.name}': {e}",
                            style="ctfa.error",
                        )
                        console.print_exception()
                        import_failed.append(challenge_folder.name)
                        break

    if unzip_failed:
        console.print(f":x: Failed to extract {len(unzip_failed)} zip file(s):", style="ctfa.error")
        for zf in unzip_failed:
            console.print(f" - {zf}", style="ctfa.error")

    if import_failed:
        console.print(f":x: Failed to import {len(import_failed)} challenge(s):", style="ctfa.error")
        for chall in import_failed:
            console.print(f" - {chall}", style="ctfa.error")

    if not no_update_stats and successful_imports > 0:
        console.print("Updating repository stats...", style="ctfa.info")
        repo.save_all_readmes()
        console.print(":sparkles: Repository stats updated.", style="ctfa.success")

    if successful_imports > 0:
        console.print(f":sparkles: Successfully imported {successful_imports} challenge(s).", style="ctfa.success")
