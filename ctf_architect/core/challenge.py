from __future__ import annotations

import os
import shutil
from pathlib import Path
from yaml import safe_load

from ctf_architect.core.config import load_config
from ctf_architect.core.models import ChallengeInfo, Service


def is_valid_challenge(path: str | Path) -> bool:
  """
  Checks if a challenge is valid.
  A challenge is considered valid if it has a chall.yaml and a README.md file.
  """
  files = os.listdir(path)
  if "chall.yaml" not in files:
    return False
  if "README.md" not in files:
    return False
  
  return True


def get_challenge_info(path: str | Path) -> ChallengeInfo:
  if isinstance(path, str):
    path = Path(path)

  if not is_valid_challenge(path):
    raise ValueError("Challenge does not have chall.yaml or README.md")
  
  with (path / "chall.yaml").open("r") as f:
    data = safe_load(f)

  info = data.get("challenge")
  if info is None:
    raise ValueError("Challenge does not specify challenge info")
  
  services = data.get("services")

  if services is not None:
    services = [
      Service(name=k, **v)
      for k, v in services.items()
    ]
  
  return ChallengeInfo.from_dict(info, services=services)


def get_services(path: str | Path) -> list[Service] | None:
  if isinstance(path, str):
    path = Path(path)

  if not is_valid_challenge(path):
    raise ValueError("Invalid challenge")
  
  with (path / "chall.yaml").open("r") as f:
    data = safe_load(f)
  
  services = data.get("services")
  if services is None:
    return None
  else:
    return [
      Service(name=k, **v)
      for k, v in services.items()
    ]


def verify_challenge_info(challenge: ChallengeInfo):
  """
  Verifies that the challenge info has valid categories and difficulties.
  """

  config = load_config()

  if challenge.category.lower() not in config.categories:
    raise ValueError(f"Invalid category: {challenge.category}")
  
  if challenge.difficulty.lower() not in config.diff_names:
    raise ValueError(f"Invalid difficulty: {challenge.difficulty}")
  

def find_challenge(name: str) -> tuple[ChallengeInfo, Path] | None:
  """
  Tries to find a challenge with the given name.

  Search method:
  1. Search by the folder name, if substring match found, check chall.yaml to verify
  2. Search every chall.yaml for a name match

  Returns a tuple of the challenge info and the path to the challenge folder.
  """
  config = load_config()

  challenges_path = Path("./challenges")

  folders: list[Path] = []
  for category in config.categories:
    for dir in (challenges_path / category).iterdir():
      if dir.is_dir():
        folders.append(dir)

  folders_searched = []

  for folder in folders:
    if name.lower() in folder.name.lower():
      folders_searched.append(folder)
      try:
        challenge = get_challenge_info(folder)
        return challenge, folder
      except ValueError:
        pass

  for folder in folders:
    if folder in folders_searched:
      continue
    try:
      challenge = get_challenge_info(folder)
      if name.lower() == challenge.name.lower():
        return challenge, folder
    except ValueError:
      pass


def add_challenge(folder: str | Path, replace: bool = False):
  """
  Adds a challenge to the challenges directory.

  If replace is True, the challenge will be replaced if it already exists.
  """
  if isinstance(folder, str):
    folder = Path(folder)

  if not folder.is_dir():
    raise ValueError("Specified path is not a directory!")
  
  challenge = get_challenge_info(folder)
  verify_challenge_info(challenge)

  # Check if challenge already exists
  if (c := find_challenge(challenge.name)) is not None:
    if replace:
      remove_challenge(c[1])
    else:
      raise FileExistsError("Challenge already exists!")
  
  
  # Move the challenge to the correct category
  new_path = Path("./challenges") / challenge.category.lower() / folder.name
  folder.rename(new_path)


def remove_challenge(name: str | None, path: Path | str | None = None):
  """
  Removes a challenge

  Either challenge name or path must be specified.

  If challenge name is specified, the challenge will be searched for and removed.
  """
  if name is None and path is None:
    raise ValueError("Either challenge name or path must be specified!")
  
  if name is not None:
    challenge = find_challenge(name)
    if challenge is None:
      raise ValueError("Challenge not found!")
    path = challenge[1]

  if isinstance(path, str):
    path = Path(path)

  if not path.is_dir():
    raise ValueError("Specified path is not a directory!")
  
  shutil.rmtree(path)