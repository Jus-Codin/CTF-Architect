from __future__ import annotations

import typer
from rich import print
from rich.table import Table

from ctf_architect.core.config import load_config
from ctf_architect.core.constants import APP_CMD_NAME
from ctf_architect.core.stats import (get_category_diff_stats, update_category_readme,
                         update_root_readme)


stats_app = typer.Typer()


@stats_app.callback()
def callback():
  """
  Commands to manage the stats of the challenge repo.
  """


@stats_app.command("update")
def stats_update():
  """
  Updates all the stats in the READMEs.
  """
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return

  try:
    for category in config.categories:
      update_category_readme(category)
    
    update_root_readme()
  except FileNotFoundError:
    print(f"[bright_red]README not found. Please run `{APP_CMD_NAME} init` first.")
  else:
    print("[green]READMEs updated successfully.")


@stats_app.command("show")
def stats_show(category: str = typer.Argument(None)):
  """
  Shows the stats of a category.

  If no category is specified, shows the stats of all categories.
  """
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return

  if category is None:
    table = Table(title="Overall Difficulty Distribution")
    # Create a table in the following format
    # | Category | Easy | Medium | ... | Total |
    # | -------- | ---- | ------ | --- | ----- |
    # | ...      | ...  | ...    | ... | ...   |
    # | ...      | ...  | ...    | ... | ...   |
    # | Total    | ...  | ...    | ... | ...   |
    table.add_column("Category", header_style="bright_cyan", style="cyan", no_wrap=True)
    for difficulty in config.diff_names:
      table.add_column(difficulty.capitalize(), header_style="magenta", style="magenta", justify="center")
    table.add_column("Total", header_style="bright_yellow", style="yellow", justify="center")

    stats = {category: get_category_diff_stats(category) for category in config.categories}

    for category in stats:
      # Check if it is the last category to add to the list
      is_last = category == config.categories[-1]
      table.add_row(
        category.capitalize(),
        *[str(stats[category][difficulty]) for difficulty in config.diff_names],
        str(sum(stats[category].values())),
        end_section=is_last
      )

    # Add the total row
    total_row = []
    for difficulty in config.diff_names:
      total_row.append(sum(stats[category][difficulty] for category in config.categories))

    table.add_row(
      "Total",
      *map(str, total_row),
      str(sum(total_row))
    )
    
  else:
    table = Table(title=f"{category.capitalize()} Difficulty Distribution")
    # Create a table in the following format
    # | Difficulty | Count |
    # | ---------- | ----- |
    # | Easy       | ...   |
    # | Medium     | ...   |
    # | ...        | ...   |
    table.add_column("Difficulty", header_style="bright_cyan", style="cyan")
    table.add_column("Count", header_style="bright_yellow", style="yellow", justify="center")

    stats = get_category_diff_stats(category)

    for difficulty, count in stats.items():
      table.add_row(difficulty.capitalize(), str(count))

  print(table)