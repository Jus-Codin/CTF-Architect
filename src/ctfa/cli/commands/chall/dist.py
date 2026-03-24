from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import shorten
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import ResolvedExistingFile

from ctfa.cli.param_types import ResolvedExistingChallengeFolder

app = App(
    name="dist",
    group="Challenge Distribution File Commands",
    help="Commands for managing challenge distribution files",
)


def _format_file(entry: object, index: int | None = None) -> str:
    from ctfa.models.challenge import StaticFile, URLFile

    if isinstance(entry, StaticFile):
        label = entry.path.as_posix()
    elif isinstance(entry, URLFile):
        label = str(entry.url)
    else:
        label = "unknown file"

    label = shorten(label, width=60, placeholder="...")
    if index is None:
        return label
    return f"{index}. {label}"


def _select_file_index(entries: list[object]) -> int:
    from ctfa.cli.ui.prompts import select

    choices = [_format_file(entry, i + 1) for i, entry in enumerate(entries)]
    return int(select("Select the distribution file", choices=choices, return_index=True).ask())


def _prompt_source_file() -> Path | None:
    from ctfa.cli.ui.prompts import input_str

    def _validate_file(value: str) -> bool | str:
        path = Path(value)
        if not path.exists():
            return "File does not exist."
        if not path.is_file():
            return "Path is not a file."
        return True

    response = input_str("Enter the file path", validator=_validate_file, allow_empty=False).ask()
    return Path(response)


def _ensure_dist_dir(challenge_path: Path) -> Path:
    dist_dir = challenge_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    return dist_dir


def add_command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    file_path: Annotated[ResolvedExistingFile | None, Parameter(name=["--file", "-f"])] = None,
    name: Annotated[str | None, Parameter(name=["--name", "-n"])] = None,
    replace: Annotated[bool, Parameter(name=["--replace", "-r"], negative="")] = False,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Add a distribution file to a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
        file_path (ResolvedExistingFile | None, optional): Path to the file to add
        name (str | None, optional): Override the destination filename in dist/
        replace (bool, optional): Replace an existing dist file with the same name
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.challenge import Challenge
    from ctfa.models.challenge import StaticFile

    chall = Challenge.load_folder(challenge_path)
    files = list(chall.config.files or [])

    if file_path is None:
        if no_interactive:
            console.print("File path is required when --no-interactive is set.", style="ctfa.error")
            return
        file_path = _prompt_source_file()
        if file_path is None:
            console.print("Aborting...", style="ctfa.error")
            return

    source_path = Path(file_path)
    target_name = name or source_path.name
    dist_dir = _ensure_dist_dir(challenge_path)
    target_path = dist_dir / target_name
    rel_path = Path("dist") / target_name

    existing_index = next(
        (i for i, entry in enumerate(files) if isinstance(entry, StaticFile) and entry.path == rel_path),
        None,
    )
    if existing_index is not None and not replace:
        console.print("A distribution file with that name is already configured.", style="ctfa.error")
        return

    if target_path.exists():
        if not replace:
            console.print("A file with that name already exists in dist/.", style="ctfa.error")
            return
        if target_path.is_dir():
            console.print("A directory with that name already exists in dist/.", style="ctfa.error")
            return
        target_path.unlink()

    if source_path.resolve() != target_path.resolve():
        shutil.copy2(str(source_path), str(target_path))

    if existing_index is None:
        files.append(StaticFile(path=rel_path))
    else:
        files[existing_index] = StaticFile(path=rel_path)

    chall.config.files = files
    chall.save()

    console.print("Distribution file added successfully.", style="ctfa.success")


def edit_command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    index: Annotated[int | None, Parameter(name=["--index", "-i"])] = None,
    file_path: Annotated[ResolvedExistingFile | None, Parameter(name=["--file", "-f"])] = None,
    name: Annotated[str | None, Parameter(name=["--name", "-n"])] = None,
    replace: Annotated[bool, Parameter(name=["--replace", "-r"], negative="")] = False,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Edit a distribution file in a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
        index (int | None, optional): The 1-based index of the file to edit
        file_path (ResolvedExistingFile | None, optional): New source file to move into dist/
        name (str | None, optional): Override the destination filename in dist/
        replace (bool, optional): Replace an existing dist file with the same name
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.prompts import input_str
    from ctfa.core.challenge import Challenge
    from ctfa.models.challenge import StaticFile

    chall = Challenge.load_folder(challenge_path)
    files = list(chall.config.files or [])

    if not files:
        console.print("No distribution files are currently defined for this challenge.", style="ctfa.warning")
        return

    if index is None:
        if no_interactive:
            console.print("File index is required when --no-interactive is set.", style="ctfa.error")
            return
        file_index = _select_file_index(files)
    else:
        if index < 1 or index > len(files):
            console.print("File index is out of range.", style="ctfa.error")
            return
        file_index = index - 1

    current_entry = files[file_index]
    if not isinstance(current_entry, StaticFile):
        console.print("Only static distribution files can be edited with this command.", style="ctfa.error")
        return

    current_rel_path = current_entry.path
    current_name = current_rel_path.name

    if file_path is None and not no_interactive:
        response = input_str(
            "Enter the new file path (leave empty to keep current)",
            allow_empty=True,
        ).ask()
        if response.strip():
            file_path = Path(response.strip())
            if not file_path.exists() or not file_path.is_file():
                console.print("File does not exist or is not a file.", style="ctfa.error")
                return

    if name is None and not no_interactive:
        response = input_str(
            "Enter the new filename (leave empty to keep current)",
            allow_empty=True,
        ).ask()
        if response.strip():
            name = response.strip()

    if file_path is None and name is None:
        if no_interactive:
            console.print("No changes specified.", style="ctfa.error")
        else:
            console.print("No changes made.", style="ctfa.warning")
        return

    source_path = Path(file_path) if file_path is not None else None
    target_name = name or (source_path.name if source_path is not None else current_name)
    dist_dir = _ensure_dist_dir(challenge_path)
    target_path = dist_dir / target_name
    rel_path = Path("dist") / target_name

    for i, entry in enumerate(files):
        if i == file_index:
            continue
        if isinstance(entry, StaticFile) and entry.path == rel_path:
            console.print("Another distribution file already uses that name.", style="ctfa.error")
            return

    if target_path.exists():
        if not replace and target_name != current_name:
            console.print("A file with that name already exists in dist/.", style="ctfa.error")
            return
        if target_path.is_dir():
            console.print("A directory with that name already exists in dist/.", style="ctfa.error")
            return

    current_path = (challenge_path / current_rel_path).resolve()

    if source_path is not None:
        if target_path.exists():
            target_path.unlink()
        shutil.copy2(str(source_path), str(target_path))
        if current_path.exists() and current_path.resolve() != target_path.resolve():
            current_path.unlink()
    elif target_name != current_name:
        if current_path.exists():
            shutil.copy2(str(current_path), str(target_path))
        else:
            console.print("Current file is missing on disk; updating config only.", style="ctfa.warning")

    files[file_index] = StaticFile(path=rel_path)
    chall.config.files = files
    chall.save()

    console.print("Distribution file updated successfully.", style="ctfa.success")


def remove_command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    index: Annotated[int | None, Parameter(name=["--index", "-i"])] = None,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Remove a distribution file from a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
        index (int | None, optional): The 1-based index of the file to remove
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.challenge import Challenge
    from ctfa.models.challenge import StaticFile

    chall = Challenge.load_folder(challenge_path)
    files = list(chall.config.files or [])

    if not files:
        console.print("No distribution files are currently defined for this challenge.", style="ctfa.warning")
        return

    if index is None:
        if no_interactive:
            console.print("File index is required when --no-interactive is set.", style="ctfa.error")
            return
        file_index = _select_file_index(files)
    else:
        if index < 1 or index > len(files):
            console.print("File index is out of range.", style="ctfa.error")
            return
        file_index = index - 1

    removed_entry = files.pop(file_index)

    if isinstance(removed_entry, StaticFile):
        dist_dir = (challenge_path / "dist").resolve()
        target_path = (challenge_path / removed_entry.path).resolve()
        if dist_dir in target_path.parents:
            if target_path.exists():
                target_path.unlink()
        else:
            console.print("Skipping file deletion outside dist/.", style="ctfa.warning")

    chall.config.files = files or None
    chall.save()

    console.print(f"Removed {_format_file(removed_entry)}.", style="ctfa.success")


app.command(add_command, name="add")
app.command(edit_command, name="edit")
app.command(remove_command, name="remove", alias="rm")
