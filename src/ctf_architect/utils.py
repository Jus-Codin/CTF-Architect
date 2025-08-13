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
