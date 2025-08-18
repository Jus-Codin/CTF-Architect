import shutil
from pathlib import Path

from ctf_architect.constants import CHALLENGE_CONFIG_FILE, CTF_CONFIG_FILE


def is_challenge_repo(path: str | Path | None = None) -> bool:
    """Checks if the current given path is a challenge repo.

    If no path is specified, the current working directory is checked.

    A challenge repo is considered valid if it has a CTF config file and a challenges directory.

    Args:
        path (str | Path, optional): The path to check. Defaults to None.

    Returns:
        bool: True if the given path is a challenge repo, False otherwise.
    """
    if path is None:
        path = Path.cwd()
    elif isinstance(path, str):
        path = Path(path)

    if path.is_dir():
        if (path / "challenges").is_dir() and (path / CTF_CONFIG_FILE).is_file():
            return True
        else:
            return False

    return False


def is_challenge_folder(path: str | Path) -> bool:
    """Checks if the specified folder is a challenge folder.

    If it has a Challenge Config file, it is considered a challenge folder.

    Args:
        path (str | Path): The path to the folder to check.

    Returns:
        bool: True if the folder is a challenge folder, False otherwise.
    """
    for file in Path(path).iterdir():
        if file.name.lower() == CHALLENGE_CONFIG_FILE:
            return True

    return False


def is_service_folder(path: str | Path) -> bool:
    """Checks if the specified folder is a service folder.

    A service folder is considered valid if it contains a Dockerfile.

    Args:
        path (str | Path): The path to the folder to check.

    Returns:
        bool: True if the folder is a service folder, False otherwise.
    """
    for file in Path(path).iterdir():
        if file.name.lower() == "dockerfile":
            return True

    return False


def copy_into(path: str | Path, targets: list[tuple[str | Path, str | Path]]) -> None:
    """Copies files or directories into the specified path.

    The destination paths must be a relative path that resolves to a file or directory in the destination folder.

    Args:
        path (Path): The destination path to copy into.
        targets (list[tuple[str | Path, str | Path]]): A list of tuples where each tuple contains the source and destination paths.
    """
    if isinstance(path, str):
        path = Path(path)

    for src, dst in targets:
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise FileNotFoundError(f"The source file {src.absolute()} does not exist.")

        # Security checks
        if dst.is_absolute() or path not in (path / dst).resolve().parents:
            raise ValueError(f"Invalid destination path: {dst.absolute()}")

        target = path / dst

        # Ensure destination exists
        target.parent.mkdir(parents=True, exist_ok=True)

        if src.is_file():
            shutil.copy(src, target)
        elif src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
