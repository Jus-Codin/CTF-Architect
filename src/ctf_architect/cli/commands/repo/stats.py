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

@app.command
def author():
    """Show challenge statistics grouped by author.

    This displays the number of challenges per difficulty for each author.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    author_stats: dict[str, dict[str, int]] = {}

    for challenge in walk_challenges():
        author = challenge.author
        diff = challenge.difficulty.lower()
        if author not in author_stats:
            author_stats[author] = {d: 0 for d in config.difficulties}
        if diff in author_stats[author]:
            author_stats[author][diff] += 1
        else:
            # Skip challenges with unknown difficulty, we might want to throw a warning here
            continue

    table = Table(title="Challenge Statistics by Author")
    table.add_column("Author", header_style="bright_cyan", style="cyan", no_wrap=True)
    for difficulty in config.difficulties:
        table.add_column(
            difficulty.capitalize(),
            header_style="bright_yellow",
            style="yellow",
            justify="center",
        )
    table.add_column("Total", header_style="bright_green", style="green", justify="center")

    for author, stats in author_stats.items():
        total = sum(stats.values())
        table.add_row(
            author,
            *[str(stats[d]) for d in config.difficulties],
            str(total),
        )

    console.print(
        Align.center(table, vertical="middle"),
        style="ctfa.info",
    )


@app.command
def filter(
    difficulty: Annotated[str | None, Parameter(name=["--difficulty", "-d"])] = None,
    category: Annotated[str | None, Parameter(name=["--category", "-c"])] = None,
):
    """Filter challenges by difficulty and/or category.

    Args:
        difficulty: The difficulty level to filter by.
        category: The category to filter by.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    challenges = list(walk_challenges())

    if difficulty is not None:
        difficulty = difficulty.lower()
        if difficulty not in config.difficulties:
            console.print(
                f"Difficulty '{difficulty}' is not recognized. Valid difficulties: {', '.join(config.difficulties)}",
                style="ctfa.error",
            )
            return
        challenges = [ch for ch in challenges if ch.difficulty.lower() == difficulty]

    if category is not None:
        category_lower = category.lower()
        if category_lower not in config.categories:
            console.print(
                f"Category '{category}' does not exist. Valid categories: {', '.join(config.categories)}",
                style="ctfa.error",
            )
            return
        challenges = [ch for ch in challenges if ch.category.lower() == category_lower]

    if not challenges:
        console.print("No challenges found with the specified filters.", style="ctfa.info")
        return
    
    table = Table(title="Filtered Challenges")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Author", style="green")

    for ch in challenges:
        table.add_row(ch.name, ch.category.capitalize(), ch.difficulty.capitalize(), ch.author)

    console.print(table)