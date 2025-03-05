"""Functions for challenge level operations."""

from __future__ import annotations

from pathlib import Path

from tomlkit import comment, document, dump, load, nl

from ctf_architect.constants import CHALLENGE_CONFIG_FILE, CHALLENGE_CONFIG_HEADER
from ctf_architect.models.challenge import Challenge, ChallengeFile
from ctf_architect.version import CHALLENGE_SPEC_VERSION


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


def load_chall_config(path: str | Path) -> Challenge:
    """Loads the challenge config from the specified path.

    Args:
        path (str | Path): The path to the challenge config file.

    Returns:
        Challenge: The challenge config.
    """
    if isinstance(path, str):
        path = Path(path)

    with open(path / CHALLENGE_CONFIG_FILE, encoding="utf-8") as f:
        data = load(f)

    config_file = ChallengeFile.model_validate(data.unwrap())

    return config_file.challenge


def save_chall_config(path: str | Path, challenge: Challenge) -> None:
    """Saves the challenge config to the specified path.

    Args:
        path (str | Path): The path to the challenge config file.
        challenge (Challenge): The challenge config.
    """
    if isinstance(path, str):
        path = Path(path)

    doc = document()

    for line in CHALLENGE_CONFIG_HEADER.splitlines():
        doc.add(comment(line))
    doc.add(nl())

    doc.add("version", str(CHALLENGE_SPEC_VERSION))  # type: ignore

    doc.add("challenge", challenge.model_dump(mode="json", exclude_defaults=True))  # type: ignore

    with open(path / CHALLENGE_CONFIG_FILE, "w", encoding="utf-8") as f:
        dump(doc, f)


def save_chall_readme(path: str | Path, challenge: Challenge) -> None:
    """Saves the challenge readme to the specified path.

    Args:
        path (str | Path): The path to the challenge readme file.
        challenge (Challenge): The challenge config.
    """
    if isinstance(path, str):
        path = Path(path)

    (path / "README.md").write_text(challenge.readme, encoding="utf-8")
