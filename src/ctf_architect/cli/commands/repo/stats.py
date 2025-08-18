from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.align import Align
from rich.table import Table

from ctf_architect.cli.ui.console import console
from ctf_architect.core.exceptions import NotInChallengeRepositoryError
from ctf_architect.core.repo import Repo
from ctf_architect.utils import calculate_difficulty_distribution

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
        repo = Repo.from_path(Path.cwd())
    except NotInChallengeRepositoryError:
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

        for difficulty in repo.ctf_config.difficulties:
            table.add_column(
                difficulty.capitalize(),
                header_style="bright_yellow",
                style="yellow",
                justify="center",
            )

        table.add_column("Total", header_style="bright_green", style="green", justify="center")

        distributions: dict[str, dict[str, int]] = {}
        for category in repo.ctf_config.categories:
            distributions[category] = {}
            for challenge in repo.walk_challenges(category=category, skip_invalid=True):
                diff = challenge.config.difficulty
                distributions[category][diff] = distributions[category].get(diff, 0) + 1

        for category in distributions:
            is_last = category == repo.ctf_config.categories[-1]
            table.add_row(
                category.capitalize(),
                *[str(distributions[category][difficulty]) for difficulty in repo.ctf_config.difficulties],
                str(sum(distributions[category].values())),
                end_section=is_last,
            )

        total_row = ["Total"]
        total_count = 0

        for difficulty in repo.ctf_config.difficulties:
            count = sum(distributions[category][difficulty] for category in distributions)
            total_row.append(str(count))
            total_count += count

        table.add_row(*total_row, str(total_count))

    elif category.lower() not in repo.ctf_config.categories:
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

        distribution = calculate_difficulty_distribution(
            [challenge.config for challenge in repo.walk_challenges(category=category, skip_invalid=True)]
        )

        for difficulty in repo.ctf_config.difficulties:
            is_last = difficulty == repo.ctf_config.difficulties[-1]
            table.add_row(
                difficulty.capitalize(),
                str(distribution[difficulty]),
                end_section=is_last,
            )

        table.add_row("Total", str(sum(distribution.values())))

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
        repo = Repo.from_path(Path.cwd())
    except NotInChallengeRepositoryError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    if update_challenges:
        for challenge in repo.walk_challenges():
            challenge.save_readme()

    repo.save_all_readmes()
    console.print("Stats updated successfully", style="ctfa.success")
