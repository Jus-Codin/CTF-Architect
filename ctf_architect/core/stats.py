from __future__ import annotations

from pathlib import Path
from warnings import warn

from ctf_architect.core.challenge import create_challenge_readme, get_chall_config
from ctf_architect.core.config import load_config
from ctf_architect.core.constants import CATEGORY_README_TEMPLATE, ROOT_README_TEMPLATE
from ctf_architect.core.models import Challenge


def get_category_difficulty_distribution(name: str) -> dict[str, int]:
    """
    Get the difficulty distribution of challenges in a category.
    """
    config = load_config()

    if name.lower() not in config.categories:
        raise ValueError(f"Category {name} does not exist")

    category_path = Path("challenges") / name.lower()

    difficulties = config.difficulties

    stats = {difficulty.name: 0 for difficulty in difficulties}

    for challenge_path in category_path.iterdir():
        if challenge_path.is_dir():
            chall_config = get_chall_config(challenge_path)

            if chall_config.difficulty.lower() not in stats:
                warn(
                    f'Ignoring unknown difficulty "{chall_config.difficulty}" in {challenge_path.absolute()}'
                )
                continue

            stats[chall_config.difficulty.lower()] += 1

    return stats


def update_challenge_readme(challenge: Challenge):
    readme = create_challenge_readme(challenge)

    with open(challenge.full_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


def update_category_readme(name: str):
    """
    Updates the category's README.md file.
    """
    config = load_config()

    if name.lower() not in config.categories:
        raise ValueError(f"Category {name} does not exist")

    category_path = Path("challenges") / name.lower()

    # Check if the category directory exists
    if not category_path.exists():
        raise FileNotFoundError(
            f"The directory {category_path.absolute()} does not exist, are you in the right directory?"
        )

    challenges: list[list[str]] = []

    for challenge_path in category_path.iterdir():
        if challenge_path.is_dir():
            config = get_chall_config(challenge_path)
            challenges.append(
                [
                    config.name,
                    config.folder_name,
                    config.description,
                    config.difficulty,
                    config.author,
                ]
            )

    # Get the difficulty distribution
    distribution = get_category_difficulty_distribution(name)

    # Create the challenges table
    challenges_table = "\n".join(
        f"| [{name}](<./{folder_name}>) |"
        + f" {description if len(description) <= 20 else description[:20]+'...'} |"
        + f" {difficulty.capitalize()} |"
        + f" {author} |"
        for name, folder_name, description, difficulty, author in challenges
    )

    # Create the difficulty distribution table
    diff_table = "\n".join(
        f"| {difficulty.capitalize()} | {count} |"
        for difficulty, count in distribution.items()
    )

    # Total row
    diff_table += f"\n| Total | {sum(distribution.values())} |"

    # Create the README
    readme = CATEGORY_README_TEMPLATE.format(
        name=name.capitalize(),
        diff_table=diff_table,
        count=len(challenges),
        challenges_table=challenges_table,
    )

    # Write the README
    with open(category_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


def update_root_readme():
    """
    Updates the root challenges README.md file.
    """
    config = load_config()

    difficulties = config.difficulties

    challenges_path = Path("challenges")

    # Check if the challenges directory exists
    if not challenges_path.exists():
        raise FileNotFoundError(
            f"The directory {challenges_path.absolute()} does not exist, are you in the right directory?"
        )

    challenges: list[list[str]] = []
    distributions: dict[str, dict[str, int]] = {}

    for category in config.categories:
        category_path = challenges_path / category.lower()

        stats = {difficulty.name: 0 for difficulty in difficulties}

        for challenge_path in category_path.iterdir():
            if challenge_path.is_dir():
                chall_config = get_chall_config(challenge_path)

                if chall_config.difficulty.lower() in stats:
                    stats[chall_config.difficulty.lower()] += 1
                else:
                    warn(
                        f'Ignoring unknown difficulty "{chall_config.difficulty}" in {challenge_path.absolute()}'
                    )

                challenges.append(
                    [
                        chall_config.name,
                        chall_config.folder_name,
                        chall_config.description,
                        category,
                        chall_config.difficulty,
                        chall_config.author,
                    ]
                )

        distributions[category] = stats

    # Create the challenges table
    challenges_table = "\n".join(
        f"| [{name}](<./{category.lower()}/{folder_name}>) |"
        + f" {description if len(description) <= 20 else description[:20]+'...'} |"
        + f" {category.capitalize()} |"
        + f" {difficulty.capitalize()} |"
        + f" {author} |"
        for name, folder_name, description, category, difficulty, author in challenges
    )

    # Create the difficulty distribution table
    diff_table_header = diff_table_header = (
        "| Category | "
        + " | ".join(d.name.capitalize() for d in config.difficulties)
        + " | Total |\n"
    )
    diff_table_header += (
        "| -------- |:"
        + ":|:".join("-" * len(diff.name) for diff in config.difficulties)
        + ":|:-----:|\n"
    )

    diff_table_body = "\n".join(
        f"| {category.capitalize()} | "
        + " | ".join(
            str(distributions[category][diff.name]) for diff in config.difficulties
        )
        + f" | {sum(distributions[category].values())} |"
        for category in config.categories
    )

    diff_table_total = (
        "| Total | "
        + " | ".join(
            str(
                sum(
                    distributions[category][diff.name] for category in config.categories
                )
            )
            for diff in config.difficulties
        )
        + f" | {sum(sum(distributions[category].values()) for category in config.categories)} |"
    )

    diff_table = f"{diff_table_header}{diff_table_body}\n{diff_table_total}\n"

    # Create the README
    readme = ROOT_README_TEMPLATE.format(
        diff_table=diff_table, count=len(challenges), challenges_table=challenges_table
    )

    # Write the README
    with open(challenges_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
