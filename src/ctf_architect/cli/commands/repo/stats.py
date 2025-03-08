from __future__ import annotations

from typing import Annotated

from cyclopts import App, Parameter
from rich.align import Align
from rich.table import Table

from ctf_architect.cli.ui.console import console
from ctf_architect.constants import APP_CMD_NAME
from ctf_architect.core.challenge import save_chall_readme
from ctf_architect.core.repo import load_repo_config, walk_challenges
from ctf_architect.core.stats import (
    get_category_difficulty_distribution,
    update_category_readme,
    update_root_readme,
)

app = App(
    name="stats",
    group="Subcommands",
    help="Commands to manage challenge repository statistics.",
)


@app.default
@app.command
def show(*, category: Annotated[str | None, Parameter(name=["--category", "-c"])] = None):
    """Show the challenge repository statistics.

    Args:
        category: The category to show statistics for.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
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

        table.add_column("Category", header_style="bright_cyan", style="cyan", no_wrap=True)

        for difficulty in config.difficulties:
            table.add_column(
                difficulty.capitalize(),
                header_style="bright_yellow",
                style="yellow",
                justify="center",
            )

        table.add_column("Total", header_style="bright_green", style="green", justify="center")

        stats = {category: get_category_difficulty_distribution(category) for category in config.categories}

        for category in stats:
            is_last = category == config.categories[-1]
            table.add_row(
                category.capitalize(),
                *[str(stats[category][difficulty]) for difficulty in config.difficulties],
                str(sum(stats[category].values())),
                end_section=is_last,
            )

        total_row = ["Total"]
        total_count = 0

        for difficulty in config.difficulties:
            count = sum(stats[category][difficulty] for category in stats)
            total_row.append(str(count))
            total_count += count

        table.add_row(*total_row, str(total_count))

    elif category.lower() not in config.categories:
        console.print(
            f"Category {category} does not exist in the repository",
            style="ctfa.error",
        )
        return

    else:
        table = Table(title=f"{category.capitalize()} Difficulty Distribution")

        # TABLE FORMAT:
        # | Difficulty | Count |
        # | ---------- | ----- |
        # | ...        | ...   |
        # | ...        | ...   |
        # | Total      | ...   |

        table.add_column("Difficulty", header_style="bright_cyan", style="cyan")
        table.add_column("Count", header_style="bright_green", style="green", justify="center")

        stats = get_category_difficulty_distribution(category)

        for difficulty in config.difficulties:
            is_last = difficulty == config.difficulties[-1]
            table.add_row(
                difficulty.capitalize(),
                str(stats[difficulty]),
                end_section=is_last,
            )

        table.add_row("Total", str(sum(stats.values())))

    console.print(
        Align.center(table, vertical="middle"),
        style="ctfa.info",
    )


@app.command
def update(
    update_challenges: Annotated[bool, Parameter(name=["--update-challenges", "-u"], negative="")] = False,
):
    """Update the challenge repository statistics.

    Args:
        update_challenges: Update all challenge READMe.md's.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    if update_challenges:
        for challenge in walk_challenges():
            save_chall_readme(challenge.repo_path, challenge)

    try:
        for category in config.categories:
            update_category_readme(category)

        update_root_readme()
    except FileNotFoundError:
        console.print(
            f"README not found. Please run `{APP_CMD_NAME} repo init` first",
            style="ctfa.error",
        )
    else:
        console.print("Stats updated successfully", style="ctfa.success")
