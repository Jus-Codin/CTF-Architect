"""
Implements challenge repo initialization.
"""

from __future__ import annotations

from pathlib import Path

from ctf_architect.core.config import load_config, save_config
from ctf_architect.core.models import CTFConfig
from ctf_architect.core.stats import update_category_readme, update_root_readme


def init_no_config(
    name: str,
    categories: list[str],
    difficulties: list[dict[str, str | int]],
    starting_port: int,
    extras: list[str] | None = None,
    config_only: bool = False,
):
    """
    Initialize a challenge repo without a config file.
    """

    config = CTFConfig(
        name=name,
        categories=categories,
        difficulties=difficulties,
        starting_port=starting_port,
        extras=extras,
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
