"""
Contains the code to initialize a new CTF repo
"""

from __future__ import annotations

from pathlib import Path

from ctf_architect.core.config import load_config, save_config
from ctf_architect.core.models import Config
from ctf_architect.core.stats import update_category_readme, update_root_readme


def init_no_config(
  categories: list[str],
  difficulties: list[dict[str, str | int]],
  port: int,
  config_only: bool = False
):
  """
  Initialize the repo with the given config.
  """
  config = Config(
    categories=categories,
    difficulties=difficulties,
    port=port
  )

  save_config(config)

  if not config_only:
    # Create the challenge folder
    Path("challenges").mkdir(exist_ok=True)

    # Create the folders for each category
    for category in categories:
      (Path("challenges") / category.lower()).mkdir(exist_ok=True)

    update_root_readme()

    for category in categories:
      update_category_readme(category)


def init_with_config():
  """
  Initialize the repo with the config in ctf_config.yaml
  """
  config = load_config()

  # Create the challenge folder
  Path("challenges").mkdir(exist_ok=True)

  # Create the folders for each category
  for category in config.categories:
    (Path("challenges") / category.lower()).mkdir(exist_ok=True)

  update_root_readme()

  for category in config.categories:
    update_category_readme(category)