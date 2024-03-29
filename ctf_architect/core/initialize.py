"""
Implements challenge repo initialization.
"""

from __future__ import annotations

from pathlib import Path

from ctf_architect.core.config import load_config, save_config
from ctf_architect.core.models import CTFConfig
from ctf_architect.core.stats import update_category_readme, update_root_readme


def init_no_config(
  categories: list[str],
  difficulties: list[dict[str, str | int]],
  port: int,
  config_only: bool = False
):
  """
  Initialize a challenge repo without a config file.
  """

  config = CTFConfig(
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
      Path(f"challenges/{category.lower()}").mkdir(exist_ok=True)

    # Update the root README
    update_root_readme()

    # Update the README for each category
    for category in categories:
      update_category_readme(category)


def init_with_config():
  """
  Initialize a challenge repo with a config file.
  """

  config = load_config()

  # Create the challenge folder
  Path("challenges").mkdir(exist_ok=True)

  # Create the folders for each category
  for category in config.categories:
    Path(f"challenges/{category.lower()}").mkdir(exist_ok=True)

  # Update the root README
  update_root_readme()

  # Update the README for each category
  for category in config.categories:
    update_category_readme(category)