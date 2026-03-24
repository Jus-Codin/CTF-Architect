from __future__ import annotations

import os
import posixpath
import re
import shutil
import unicodedata
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

from ruamel.yaml import YAML

from ctfa.constants import CHALLENGE_CONFIG_FILE, CTF_CONFIG_FILE

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ctfa.models.challenge import ChallengeConfig

# ----------------------------------------------------------------
# File and Folder Utilities
# ----------------------------------------------------------------


def get_ctf_config_file(path: str | Path) -> Path | None:
    """Gets the CTF config file in the specified path.

    Args:
        path (str | Path): The path to search for the CTF config file.

    Returns:
        Path | None: The path to the CTF config file if found, None otherwise.
    """
    if isinstance(path, str):
        path = Path(path)

    if not path.exists() or not path.is_dir():
        return None

    ctf_config_file = path / CTF_CONFIG_FILE
    if ctf_config_file.is_file():
        return ctf_config_file

    return None


def is_challenge_repo(path: str | Path) -> bool:
    """Checks if the current given path is a challenge repo.

    A challenge repo is considered valid if it has a `ctf_config.yaml` file and a challenges directory.

    Args:
        path (str | Path): The path to check.

    Returns:
        bool: True if the given path is a challenge repo, False otherwise.
    """
    if isinstance(path, str):
        path = Path(path)

    if path.exists() and path.is_dir() and (path / "challenges").exists() and (path / "challenges").is_dir():
        ctf_config_file = get_ctf_config_file(path)
        if ctf_config_file is not None:
            return True

    return False


def get_challenge_config_file(path: str | Path) -> Path | None:
    """Gets the Challenge config file in the specified path.

    Args:
        path (str | Path): The path to search for the Challenge config file.

    Returns:
        Path | None: The path to the Challenge config file if found, None otherwise.
    """
    if isinstance(path, str):
        path = Path(path)

    if not path.exists() or not path.is_dir():
        return None

    challenge_config_file = path / CHALLENGE_CONFIG_FILE
    if challenge_config_file.is_file():
        return challenge_config_file

    return None


def is_challenge_folder(path: str | Path) -> bool:
    """Checks if the specified folder is a challenge folder.

    If it has a `chall.yaml` file, it is considered a challenge folder.

    Args:
        path (str | Path): The path to the folder to check.

    Returns:
        bool: True if the folder is a challenge folder, False otherwise.
    """
    return get_challenge_config_file(path) is not None


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


FileStructureDict: TypeAlias = dict[str, "str | None | Iterable[str] | FileStructureDict"]
"""A dictionary representing a file structure for building a folder tree.

The keys are the names of files or folders, and the values can be:
- str: Represents a file or folder path to copy from. An empty string creates an empty file.
- None: Creates an empty file at the specified key location.
- Iterable[str]: Represents a folder containing the listed files or subfolders.
- FileStructureDict: Represents a nested folder structure. An empty dict creates an empty folder.

The special key "." can be used to represent the current directory.
"""


def build_file_structure(structure: FileStructureDict, base_path: str | Path) -> None:
    """Builds a file structure in the specified base path.

    WARNING: This function is a non-atomic operation, and may fail halfway through.

    Args:
        structure (FileStructureDict): The file structure to build.
        base_path (str | Path): The base path to build the structure in.
    """
    if isinstance(base_path, str):
        base_path = Path(base_path)

    # For security, we should check if any values are attempting to write outside the base path
    # To achieve this, we build a mapping of all the paths we will create

    def _build_targets(current_structure: FileStructureDict, current_base: Path) -> list[tuple[Path | None, Path, str]]:
        # List of (FROM, TO, TYPE) tuples where TYPE is "copy", "empty_file", or "empty_dir"
        items: list[tuple[Path | None, Path, str]] = []

        for name, content in current_structure.items():
            # Try to sanitize the destination path
            target_path = safe_join(current_base, name)
            if target_path is None:
                raise ValueError(f"Invalid path detected in structure: {name}")
            target_path = Path(target_path)

            # Handle None -> create empty file
            if content is None:
                items.append((None, target_path, "empty_file"))
            # Handle nested structures
            elif isinstance(content, dict):
                if len(content) == 0:
                    # Empty dict -> create empty folder
                    items.append((None, target_path, "empty_dir"))
                else:
                    # Non-empty dict -> create folder and recurse
                    items.extend(_build_targets(content, target_path))
            # Handle single file or folder
            elif isinstance(content, str):
                if len(content) == 0:
                    # Empty string -> create empty file
                    items.append((None, target_path, "empty_file"))
                else:
                    # Single file or folder to copy
                    items.append((Path(content), target_path, "copy"))
            # Handle iterable of files or folders into a folder
            else:
                for item in content:
                    item_path = safe_join(current_base, item)
                    if item_path is None:
                        raise ValueError(f"Invalid path detected in structure: {item}")
                    items.append((Path(item_path), current_base, "copy"))

        return items

    targets = _build_targets(structure, base_path)

    # Separate copy operations from create operations
    copy_targets = []

    # Create empty files and directories first
    for src, dst, typ in targets:
        if typ == "empty_file":
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.touch()
        elif typ == "empty_dir":
            dst.mkdir(parents=True, exist_ok=True)
        elif typ == "copy":
            copy_targets.append((src, dst))

    # Then handle copy operations
    if copy_targets:
        copy_into(base_path, copy_targets)


def copy_into(base_path: str | Path, targets: list[tuple[str | Path, str | Path]]) -> None:
    """Copies files or directories into the specified path.

    WARNING: This function may not be secure, ensure that the targets have already been validated, or come from a trusted source.

    The destination paths must resolve to a path within the specified base path, and must be the exact path to copy into.

    Args:
        base_path (Path): The base path to copy into.
        targets (list[tuple[str | Path, str | Path]]): A list of tuples where each tuple contains the source and destination paths.
    """
    if isinstance(base_path, str):
        base_path = Path(base_path)

    # Throw a warning if base_path is not absolute
    if not base_path.is_absolute():
        warnings.warn(
            f'base_path "{base_path}" is not absolute. It is recommended to use absolute paths for security reasons.',
            UserWarning,
        )

    base_path = base_path.resolve()

    for src, dst in targets:
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise FileNotFoundError(f"The source file {src.absolute()} does not exist.")

        # Resolve to absolute paths
        if dst.is_absolute():
            target = dst.resolve()
        else:
            target = safe_join(base_path, dst.as_posix())
            if target is None:
                raise ValueError(f"Invalid destination path: {dst.absolute()}")
            target = Path(target).resolve()

        # Security: Ensure target is within base_path
        if base_path not in target.parents:
            raise ValueError(f"Destination path {target} is outside of the base path {base_path}.")

        # Ensure destination exists
        target.parent.mkdir(parents=True, exist_ok=True)

        if src.is_file():
            shutil.copy(src, target)
        elif src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)


# ----------------------------------------------------------------
# Security Utilities
# ----------------------------------------------------------------

_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
_windows_device_files = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}
_os_alt_seps: list[str] = list(sep for sep in [os.sep, os.path.altsep] if sep is not None and sep != "/")


def secure_filename(filename: str) -> str:
    r"""Pass it a filename and it will return a secure version of it.

    This filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.

    Taken from Flask's werkzeug.utils.secure_filename

    On windows systems the function also makes sure that the file is not
    named after one of the special device files.

    >>> secure_filename("My cool movie.mov")
    'My_cool_movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename('i contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'

    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.
    """
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    for sep in os.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip("._")

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if os.name == "nt" and filename and filename.split(".")[0].upper() in _windows_device_files:
        filename = f"_{filename}"

    return filename


def safe_join(directory: str | Path, *pathnames: str) -> str | None:
    """Safely join zero or more untrusted path components to a base directory to avoid escaping the base directory.

    Taken from Flask's werkzeug.security.safe_join
    """
    if directory == "":
        # Ensure we end up with ./path if directory="" is given,
        # otherwise the first untrusted part could become trusted.
        directory = "."

    parts = [directory]

    for filename in pathnames:
        if filename != "":
            filename = posixpath.normpath(filename)

        if (
            any(sep in filename for sep in _os_alt_seps)
            or os.path.isabs(filename)
            # ntpath.isabs doesn't catch this on Python < 3.11
            or filename.startswith("/")
            or filename == ".."
            or filename.startswith("../")
        ):
            return None

        parts.append(filename)

    return posixpath.join(*parts)


# ----------------------------------------------------------------
# Challenge Analysis Utilities
# ----------------------------------------------------------------


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


# ----------------------------------------------------------------
# LRU Cache
# ----------------------------------------------------------------


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
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            raise KeyError(f"Key {key} not found in cache.")

    def __setitem__(self, key: _KT, value: _VT):
        """Set an item in the cache."""
        self.put(key, value)


# ----------------------------------------------------------------
# Sentinel MISSING
# ----------------------------------------------------------------


class _MISSING_TYPE:
    def __repr__(self):
        return "<MISSING>"


MISSING = _MISSING_TYPE()


# ----------------------------------------------------------------
# YAML Helpers
# ----------------------------------------------------------------


yaml = YAML()
yaml.default_flow_style = False
yaml.indent(mapping=2, sequence=4, offset=2)


def _multiline_str_representer(dumper, data: str):
    if "\n" in data:  # Check if the string is multiline
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.Representer.add_representer(str, _multiline_str_representer)

# ----------------------------------------------------------------
# String Utilities
# ----------------------------------------------------------------


def slugify(s: str) -> str | None:
    """Generate a valid slug string from the given string.

    A slug string must follow the pattern `^[a-z][a-z0-9_-]*$`. This is achieved by:
    - Converting the string to lowercase.
    - Replacing spaces and invalid characters with hyphens.
    - Removing leading characters until a letter is found.
    - Stripping leading and trailing hyphens.

    Args:
        s (str): The string to slugify.

    Returns:
        str | None: The slugified string, or None if it cannot be converted.
    """
    slug = s.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"^[^a-z]+", "", slug)
    slug = slug.strip("-")
    return slug or None
