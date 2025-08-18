import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Any, Generic, TypeVar

from ctf_architect.constants import CHALLENGE_CONFIG_FILE, CTF_CONFIG_FILE
from ctf_architect.models.challenge import ChallengeConfig


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


def calculate_difficulty_distribution(challenges: list[ChallengeConfig]) -> dict[str, int]:
    """Calculates the difficulty distribution of a given list of challenges.

    Args:
        challenges (list[ChallengeConfig]): The list of challenges to analyze.

    Returns:
        dict[str, int]: A dictionary mapping difficulty levels to their respective counts.
    """
    distribution = {}
    for challenge in challenges:
        difficulty = challenge.difficulty
        distribution[difficulty] = distribution.get(difficulty, 0) + 1
    return distribution


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T", bound=Any)


class LRUCache(Generic[_KT, _VT]):
    """LRU cache implementation that allows for key removal."""

    def __init__(self, max_size: int):
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, key: _KT, default: _T | None = None) -> _VT | _T | None:
        """Get an item from the cache."""
        if key not in self.cache:
            return default
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: _KT, value: _VT) -> None:
        """Put an item into the cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def pop(self, key: _KT, default: _T | None = None) -> _VT | _T | None:
        """Remove an item from the cache."""
        if key not in self.cache:
            return default
        else:
            return self.cache.pop(key)

    def clear(self):
        """Clear the cache."""
        self.cache.clear()

    def keys(self):
        """Get all keys from the cache."""
        return self.cache.keys()

    def values(self):
        """Get all values from the cache."""
        return self.cache.values()

    def items(self):
        """Get all items from the cache."""
        return self.cache.items()

    def __len__(self):
        """Get the current size of the cache."""
        return len(self.cache)

    def __contains__(self, key: _KT) -> bool:
        """Check if a key is in the cache."""
        return key in self.cache

    def __getitem__(self, key: _KT) -> _VT:
        """Get an item from the cache."""
        return self.cache[key]

    def __setitem__(self, key: _KT, value: _VT):
        """Set an item in the cache."""
        self.cache[key] = value
