from __future__ import annotations

from pathlib import Path

from ctf_architect.core.challenge import get_challenge_info
from ctf_architect.core.config import load_config


CATEGORY_README_TEMPLATE = """# {name} Challenges
This directory contains challenges related to {name}.

## Challenges ({count} total)
| Name | Description | Difficulty | Author |
| ---- | ----------- | ---------- | ------ |
{challenges_table}

## Difficulty Distribution
| Difficulty | Number of Challenges |
| ---------- |:--------------------:|
{diff_table}
"""

ROOT_README_TEMPLATE = """# Challenges
This directory contains all challenges.

## Challenges ({count} total)
| Name | Description | Category | Difficulty | Author |
| ---- | ----------- | -------- | ---------- | ------ |
{challenges_table}

## Difficulty Distribution
{diff_table}
"""


def get_category_diff_stats(name: str) -> dict[str, int]:
  """
  Gets the difficulty distribution of a category.
  """
  config = load_config()

  if name.lower() not in config.categories:
    raise ValueError(f"Category {name} does not exist.")
  
  category_path = Path("challenges") / name.lower()

  difficulties = config.difficulties

  stats = {difficulty["name"]: 0 for difficulty in difficulties}

  for challenge_path in category_path.iterdir():
    if challenge_path.is_dir():
      info = get_challenge_info(challenge_path)
      stats[info.difficulty.lower()] += 1

  return stats


def update_category_readme(name: str):
  """
  Updates the category's README.md file.
  """
  config = load_config()

  if name.lower() not in config.categories:
    raise ValueError(f"Category {name} does not exist.")
  
  challenges_path = Path("challenges")

  # Check if the challenges directory exists
  if not challenges_path.exists():
    raise FileNotFoundError("Challenges directory does not exist, are you sure you are in the right directory?")
  
  category_path = challenges_path / name.lower()

  # Get all challenge info
  challenges: list[list[str]] = []
  
  for challenge_path in category_path.iterdir():
    if challenge_path.is_dir():
      info = get_challenge_info(challenge_path)
      challenges.append([info.name, info.description, info.difficulty, info.author])

  # Get the difficulty stats
  stats = get_category_diff_stats(name)

  # Create the challenges table
  newline = "\n"
  challenges_table = "\n".join(
    f"| [{name}](<../{name}>) | {description.replace(newline, '')} | {difficulty.capitalize()} | {author} |"
    for name, description, difficulty, author in challenges
  )

  # Create the difficulty table
  diff_table = "\n".join(
    f"| {difficulty.capitalize()} | {count} |"
    for difficulty, count in stats.items()
  )

  # Add the total row
  diff_table += f"\n| Total | {sum(stats.values())} |"

  # Create the README
  readme = CATEGORY_README_TEMPLATE.format(
    name=name.capitalize(),
    count=len(challenges),
    challenges_table=challenges_table,  
    diff_table=diff_table
  )

  # Write the README
  with (category_path / "README.md").open("w") as f:
    f.write(readme)


def update_root_readme():
  """
  Updates the root challenges README.md file.
  """
  config = load_config()

  challenges_path = Path("challenges")

  # Check if the challenges directory exists
  if not challenges_path.exists():
    raise FileNotFoundError("Challenges directory does not exist, are you sure you are in the right directory?")

  # Get all challenge info
  challenges: list[list[str]] = []
  
  for category in config.categories:
    category_path = challenges_path / category.lower()

    for challenge_path in category_path.iterdir():
      if challenge_path.is_dir():
        info = get_challenge_info(challenge_path)
        challenges.append([info.name, info.description, info.category, info.difficulty, info.author])

  # Get the difficulty stats
  stats = {category: get_category_diff_stats(category) for category in config.categories}

  # Create the challenges table
  newline = "\n"
  challenges_table = "\n".join(
    f"| [{name}](<../{category}/{name}>) | {description.replace(newline, '')} | {category.capitalize()} | {difficulty.capitalize()} | {author} |"
    for name, description, category, difficulty, author in challenges
  )

  # Create the difficulty table
  diff_table_header = "| Category | " + " | ".join(d.capitalize() for d in config.diff_names) + " | Total |\n"
  diff_table_header += "| -------- |:" + ":|:".join("-" * len(diff) for diff in config.diff_names) + ":|:-----:|\n"

  diff_table_body = "\n".join(
    f"| {category.capitalize()} | " + " | ".join(str(stats[category][diff]) for diff in config.diff_names) + f" | {sum(stats[category].values())} |"
    for category in stats
  )

  diff_table_total = (
    "\n| Total | " +
    " | ".join(str(sum(stats[category][diff] for category in config.categories)) for diff in config.diff_names) +
    f" | {sum(sum(stats[category].values()) for category in config.categories)} |\n"
  )

  diff_table = diff_table_header + diff_table_body + diff_table_total

  # Create the README
  readme = ROOT_README_TEMPLATE.format(
    count=len(challenges),
    challenges_table=challenges_table,  
    diff_table=diff_table
  )

  # Write the README
  with (challenges_path / "README.md").open("w") as f:
    f.write(readme)