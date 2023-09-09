"""
Functions to create a new challenge folder.

Challenge template:
<challenge name>
├── dist
│   └── <files to give participants here>
├── service
│   └── <service name>
│       ├── dockerfile
│       └── <other files>
├── solution
│   ├── writeup.md
│   └── <optional solve scripts, etc>
├── chall.yaml
└── README.md
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TypedDict

from yaml import safe_dump

from ctf_architect.core.models import ChallengeInfo, Flag, Hint, Service


class ServiceDict(TypedDict):
  name: str
  path: str
  port: int


README_TEMPLATE = """# {name}
{description}

## Summary
- **Author:** {author}
- **Discord Username:** {discord}
- **Category:** {category}
- **Difficulty:** {difficulty}

## Hints
{hints}

## Files
{files}

## Services
{services}

## Flags
{flags}
"""


def create_challenge_readme(info: ChallengeInfo) -> str:
  """
  Creates a README.md file for a challenge.
  """
  flags = "\n".join([
    f"- `{flag.flag}` ({'regex' if flag.regex else 'static'})"
    for flag in info.flags
  ])
  
  if info.hints is None:
    hints = "None"
  else:
    hints = "\n".join([f"- `{hint.description}` ({hint.cost} points)" for hint in info.hints])
  
  if info.files is None:
    files = "None"
  else:
    files = ""
    for file in info.files:
      path = Path(file)
      files += f"- [`{path.name}`]({path})\n"
  
  if info.services is None:
    services = "None"
  else:
    services = ""
    for service in info.services:
      services += f"- [`{service.name}`]({service.path}) (port {service.port})\n"
  
  return README_TEMPLATE.format(
    name=info.name,
    description=info.description,
    author=info.author,
    discord=info.discord,
    category=info.category,
    difficulty=info.difficulty,
    hints=hints,
    files=files,
    services=services,
    flags=flags
  )


def create_challenge_folder(name: str, dist: bool = False, service: bool = False) -> Path:
  """
  Creates a folder with the challenge template.
  """
  challenge_path = Path(name)
  challenge_path.mkdir(exist_ok=True)

  if dist:
    (challenge_path / "dist").mkdir(exist_ok=True)

  if service:
    (challenge_path / "service").mkdir(exist_ok=True)

  (challenge_path / "solution").mkdir(exist_ok=True)

  # Create empty files
  (challenge_path / "chall.yaml").touch()
  (challenge_path / "README.md").touch()

  return challenge_path



def create_challenge(
  name: str,
  description: str,
  difficulty: str,
  category: str,
  author: str,
  discord: str,
  solution_files: list[Path],
  flag: str =  None,
  flags: list[dict[str, str | bool]] = None,
  hints: dict[str, str | int] = None,
  files: list[Path] = None,
  requirements: list[str] = None,
  services: list[ServiceDict] = None
) -> Path:
  """
  Creates a folder with the challenge template.

  Parameters
  ----------
  name : str
    The name of the challenge.
  description : str
    The description of the challenge.
  difficulty : str
    The difficulty of the challenge.
  category : str
    The category of the challenge.
  author : str
    The author of the challenge.
  discord : str
    The discord of the author.
  flag : str, optional
    The flag of the challenge.
  flags : list[dict[str, str | bool]], optional
    The flags of the challenge.
  hints : dict[str, str | int], optional
    The hints of the challenge.
  files : list[Path], optional
    Paths to the files that should be given to participants
  requirements : list[str], optional
    The requirements of the challenge.
  services : list[ServiceDict], optional
    The services of the challenge.

  Returns
  -------
  Path
    The path to the challenge folder.
  """

  if flag is None and flags is None:
    raise ValueError("Must specify either flag or flags")
  elif flag is not None and flags is not None:
    raise ValueError("Cannot specify both flag and flags")
  
  if flag is not None:
    flags = [Flag(flag=flag)]

  if flags is not None:
    flags = [Flag(**flag) for flag in flags]

  if hints is not None:
    hints = [Hint(**hint) for hint in hints]
  
  dist = files is not None
  service = services is not None

  path = create_challenge_folder(name, dist=dist, service=service)

  if files is not None:
    # Copy files to dist folder
    file_paths = []
    for file in files:
      file_path = shutil.copy(file, path / "dist")
      file_path = Path(file_path).relative_to(path)
      file_paths.append(file_path.as_posix())
  else:
    file_paths = None

  if services is not None:
    # Copy services to service folder
    service_objs = []
    for service in services:
      service_path = path / "service" / service["name"]
      shutil.copytree(service["path"], service_path)
      service_obj = Service(service["name"], path=service_path.relative_to(path).as_posix(), port=str(service["port"]))
      service_objs.append(service_obj)
  else:
    service_objs = None

  # Copy solution files to solution folder
  for file in solution_files:
    shutil.copy(file, path / "solution")

  # Create challenge info
  info = ChallengeInfo(
    name=name,
    description=description,
    difficulty=difficulty,
    category=category,
    author=author,
    discord=discord,
    flags=flags,
    hints=hints,
    files=file_paths,
    requirements=requirements,
    services=service_objs
  )

  # Save challenge info in chall.yaml
  safe_dump(info.to_dict(), (path / "chall.yaml").open("w"))

  # Create README.md
  (path / "README.md").write_text(create_challenge_readme(info))

  return path