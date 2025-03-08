from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from warnings import warn

from ctf_architect.constants import (
    CATEGORY_README_TEMPLATE,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    ROOT_README_TEMPLATE,
)
from ctf_architect.core.challenge import is_challenge_folder, load_chall_config
from ctf_architect.core.exceptions import InvalidCategoryError
from ctf_architect.core.repo import load_repo_config, walk_challenge_folders


def get_category_difficulty_distribution(name: str) -> dict[str, int]:
    """Get the difficulty distribution of challenges in a category.

    Args:
        name (str): The name of the category.

    Returns:
        dict[str, int]: A dictionary with the difficulty names as keys and the number of challenges in each difficulty as values.

    Raises:
        InvalidCategoryError: If the category does not exist.
    """
    config = load_repo_config()

    if name.lower() not in config.categories:
        raise InvalidCategoryError(f"Category {name} does not exist")

    category_path = Path("challenges") / name.lower()

    difficulties = config.difficulties

    stats = {difficulty: 0 for difficulty in difficulties}

    for challenge_path in category_path.iterdir():
        if challenge_path.is_dir() and is_challenge_folder(challenge_path):
            chall_config = load_chall_config(challenge_path)

            if chall_config.difficulty.lower() not in stats:
                warn(f'Ignoring unknown difficulty "{chall_config.difficulty}" in {challenge_path.absolute()}')
                continue

            stats[chall_config.difficulty.lower()] += 1

    return stats


def update_category_readme(name: str):
    """Update the category's README.md file.

    Args:
        name (str): The name of the category.
    """
    config = load_repo_config()

    challenges: list[tuple[str, str, str, str, str]] = []
    services: list[tuple[str, str, str, str, str, str]] = []

    for challenge_path in walk_challenge_folders(name):
        config = load_chall_config(challenge_path)
        challenges.append(
            (
                shorten(config.name, MAX_NAME_LENGTH, placeholder="..."),
                config.folder_name,
                shorten(config.description, MAX_DESCRIPTION_LENGTH, placeholder="..."),
                config.difficulty.capitalize(),
                config.author,
            )
        )

        if config.services is not None:
            for service in config.services:
                services.append(
                    (
                        shorten(config.name, MAX_NAME_LENGTH, placeholder="..."),
                        config.folder_name,
                        shorten(service.name, MAX_NAME_LENGTH, placeholder="..."),
                        service.path.as_posix(),
                        ", ".join(map(str, service.ports_list)) or "None",
                        service.type,
                    )
                )

    distribution = get_category_difficulty_distribution(name)

    if len(challenges) == 0:
        challenges_table = "None"
        services_table = "None"
    else:
        challenges_table = (
            "| Name | Folder | Description | Difficulty | Author |\n"
            "|------|--------|-------------|------------|--------|\n"
        )
        challenges_table += "\n".join(
            f"| [{name}](<./{folder}>) | [{folder}](<./{folder}>) | {description} | {difficulty} | {author} |"
            for name, folder, description, difficulty, author in challenges
        )

        services_table = "| Service | Challenge | Ports | Type |\n|---------|-----------|-------|------|\n"
        services_table += "\n".join(
            f"| [{service_name}](<./{folder}/{service_path}>) | [{name}](<./{folder}>) | {ports} | {service_type} |"
            for name, folder, service_name, service_path, ports, service_type in services
        )

    diff_table = "\n".join(f"| {difficulty.capitalize()} | {count} |" for difficulty, count in distribution.items())
    diff_table += f"\n| **Total** | **{sum(distribution.values())}** |"

    category_readme = CATEGORY_README_TEMPLATE.format(
        name=name.capitalize(),
        diff_table=diff_table,
        count=len(challenges),
        challenges_table=challenges_table,
        service_count=len(services),
        services_table=services_table,
    )

    with open(f"challenges/{name.lower()}/README.md", "w", encoding="utf-8") as f:
        f.write(category_readme)


def update_root_readme():
    """Update the root challenges README.md file."""
    config = load_repo_config()

    challenges_path = Path("challenges")

    challenges: list[tuple[str, str, str, str, str, str]] = []
    services: list[tuple[str, str, str, str, str, str, str]] = []
    distributions: dict[str, dict[str, int]] = {}

    for category in config.categories:
        distributions[category] = get_category_difficulty_distribution(category)

        category_path = challenges_path / category.lower()

        for challenge_path in category_path.iterdir():
            if challenge_path.is_dir() and is_challenge_folder(challenge_path):
                chall_config = load_chall_config(challenge_path)

                challenges.append(
                    (
                        shorten(chall_config.name, MAX_NAME_LENGTH, placeholder="..."),
                        chall_config.folder_name,
                        shorten(
                            chall_config.description,
                            MAX_DESCRIPTION_LENGTH,
                            placeholder="...",
                        ),
                        category,
                        chall_config.difficulty.capitalize(),
                        chall_config.author,
                    )
                )

                if chall_config.services is not None:
                    for service in chall_config.services:
                        services.append(
                            (
                                shorten(
                                    chall_config.name,
                                    MAX_NAME_LENGTH,
                                    placeholder="...",
                                ),
                                chall_config.folder_name,
                                shorten(service.name, MAX_NAME_LENGTH, placeholder="..."),
                                service.path.as_posix(),
                                category,
                                ", ".join(map(str, service.ports_list)) or "None",
                                service.type,
                            )
                        )

    if len(challenges) == 0:
        challenges_table = "None"
        services_table = "None"
    else:
        challenges_table = (
            "| Name | Folder | Description | Category | Difficulty | Author |\n"
            "|------|--------|-------------|----------|------------|--------|\n"
        )
        challenges_table += "\n".join(
            f"| [{name}](<./{category.lower()}/{folder}>) | [{folder}](<./{category.lower()}/{folder}>) | {description} | {category.capitalize()} | {difficulty} | {author} |"
            for name, folder, description, category, difficulty, author in challenges
        )

        services_table = (
            "| Service | Challenge | Category | Ports | Type |\n|---------|-----------|----------|-------|------|\n"
        )
        services_table += "\n".join(
            f"| [{service_name}](<./{category.lower()}/{folder}/{service_path}>) | [{name}](<./{category.lower()}/{folder}>) | {category.capitalize()} | {ports} | {service_type} |"
            for name, folder, service_name, service_path, category, ports, service_type in services
        )

    diff_table_header = (
        "| Category | " + " | ".join(difficulty.capitalize() for difficulty in config.difficulties) + " | Total |\n"
    )
    diff_table_header += "|----------|:" + ":|:".join("-" * len(difficulty) for difficulty in config.difficulties)
    diff_table_header += ":|:-----:|"

    diff_table_body = "\n".join(
        f"| {category.capitalize()} | "
        + " | ".join(str(distributions[category][difficulty]) for difficulty in config.difficulties)
        + f" | {sum(distributions[category].values())} |"
        for category in config.categories
    )

    diff_table_total = (
        "| **Total** |"
        + " | ".join(
            str(sum(distributions[category][difficulty] for category in config.categories))
            for difficulty in config.difficulties
        )
        + f" | {sum(sum(distributions[category].values()) for category in config.categories)} |"
    )

    diff_table = f"{diff_table_header}\n{diff_table_body}\n{diff_table_total}\n"

    root_readme = ROOT_README_TEMPLATE.format(
        diff_table=diff_table,
        count=len(challenges),
        challenges_table=challenges_table,
        service_count=len(services),
        services_table=services_table,
    )

    (challenges_path / "README.md").write_text(root_readme, encoding="utf-8")
