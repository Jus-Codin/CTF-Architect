from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ctf_architect.core.challenge import walk_challenges
from ctf_architect.core.config import load_config
from ctf_architect.core.constants import APP_CMD_NAME
from ctf_architect.core.stats import (
    get_category_difficulty_distribution,
    update_category_readme,
    update_challenge_readme,
    update_root_readme,
)

console = Console()


stats_app = typer.Typer()


@stats_app.callback()
def callback():
    """
    Commands to manage challenge statistics in the challenge repository
    """


@stats_app.command("update")
def stats_update(
    update_challenges: bool = typer.Option(
        False, "--update-challenges", "-u", help="Update all challenge READMe.md's"
    ),
):
    """
    Update the challenge statistics in the challenge repository
    """
    try:
        config = load_config()
    except FileNotFoundError:
        console.print(
            "Could not find CTF config file. Are you in the right directory?",
            style="bright_red",
        )
        return

    if update_challenges:
        for challenge in walk_challenges():
            update_challenge_readme(challenge)

    try:
        for category in config.categories:
            update_category_readme(category)

        update_root_readme()
    except FileNotFoundError:
        console.print(
            f"README not found. Please run `{APP_CMD_NAME} init` first",
            style="bright_red",
        )
    else:
        console.print("Stats updated successfully", style="green")


@stats_app.command("show")
def stats_show(category: str | None = typer.Argument(None)):
    """
    Shows the stats of a category.

    If no category is provided, shows the stats of all categories.
    """
    try:
        config = load_config()
    except FileNotFoundError:
        console.print(
            "Could not find CTF config file. Are you in the right directory?",
            style="bright_red",
        )
        return

    if category is None:
        table = Table(title="Overall Difficulty Distribution")
        # TABLE FORMAT:
        # | Category | Easy | Medium | ... | Total |
        # | -------- | ---- | ------ | --- | ----- |
        # | ...      | ...  | ...    | ... | ...   |
        # | ...      | ...  | ...    | ... | ...   |
        # | Total    | ...  | ...    | ... | ...   |
        table.add_column(
            "Category", header_style="bright_cyan", style="cyan", no_wrap=True
        )
        for difficulty in config.difficulties:
            table.add_column(
                difficulty.name,
                header_style="bright_magenta",
                style="magenta",
                justify="center",
            )
        table.add_coloumn(
            "Total", header_style="bright_green", style="green", justify="center"
        )

        stats = {
            category: get_category_difficulty_distribution(category)
            for category in config.categories
        }

        for category in stats:
            is_last = category == config.categories[-1]
            table.add_row(
                category.capitalize(),
                *[
                    str(stats[category][difficulty.name])
                    for difficulty in config.difficulties
                ],
                str(sum(stats[category].values())),
                end_section=is_last,
            )

        total_row = ["Total"]
        total_count = 0

        for difficulty in config.difficulties:
            count = sum(stats[category][difficulty.name] for category in stats)
            total_row.append(str(count))
            total_count += count

        table.add_row(*total_row, str(total_count))

    elif category.lower() not in config.categories:
        console.print(f'Unknown category "{category}"', style="bright_red")
        return

    else:
        table = Table(title=f"Difficulty Distribution for {category.capitalize()}")
        # TABLE FORMAT:
        # | Difficulty | Count |
        # | ---------- | ----- |
        # | ...        | ...   |
        # | ...        | ...   |
        # | Total      | ...   |
        table.add_column("Difficulty", header_style="bright_cyan", style="cyan")
        table.add_column(
            "Count", header_style="bright_green", style="green", justify="center"
        )

        stats = get_category_difficulty_distribution(category)

        for difficulty in config.difficulties:
            is_last = difficulty == config.difficulties[-1]
            table.add_row(
                difficulty.name, str(stats[difficulty.name]), end_section=is_last
            )

        table.add_row("Total", str(sum(stats.values())))

    console.print(table)
