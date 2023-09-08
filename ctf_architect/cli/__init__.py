from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from ctf_architect.cli.challenge import challenge_app
from ctf_architect.cli.stats import stats_app
from ctf_architect.initialize import init_no_config, init_with_config

app = typer.Typer()
app.add_typer(challenge_app, name="challenge")
app.add_typer(stats_app, name="stats")


@app.command()
def init(
  port: int = typer.Option(8000, "--port", "-p", help="Specify the port."),
  config_only: bool = typer.Option(False, "--config-only", "-c", help="Only create the config file.")
):
  """
  Initialize a new CTF repo.
  """

  if config_only and Path("ctf_config.yaml").exists():
    print("[bright_red]ctf_config.yaml already exists.[/bright_red]")
    return
  
  # Check if there is a ctf_config.yaml in the current directory, if so, use that config
  # Otherwise, use the config specified in the command line arguments
  if Path("ctf_config.yaml").exists():
    try:
      init_with_config()
    except ValueError as e:
      print(f"[bright_red]{e}[/bright_red]")
      return
    else:
      print("[bright_green]Initialized CTF repo with config in ctf_config.yaml.[/bright_green]")
  
  else:
    # Get the categories and difficulties from the user
    categories = []
    difficulties = []

    print("[bold yellow]Please enter the categories for your CTF. Enter an empty string to stop.[/]")
    while True:
      category = typer.prompt("Category name", default="", show_default=False)
      if category == "":
        break
      categories.append(category.lower())

      print(f"\n[bold yellow]Category {category} added.[/]\n")

    if len(categories) == 0:
      print("[bright_red]Please specify at least one category.[/bright_red]")
      return

    print("\n[bold yellow]Please enter the difficulties for your CTF. Enter an empty string to stop.[/]")
    while True:
      name = typer.prompt("Difficulty name", default="", show_default=False)
      if name == "":
        break
      value = typer.prompt("Difficulty value", type=int, default=500)
      difficulties.append({
        "name": name.lower(),
        "value": value
      })

      print(f"\n[bold yellow]Difficulty {name} added. ({value} points)[/]\n")
    
    if len(difficulties) == 0:
      print("[bright_red]Please specify at least one difficulty.[/bright_red]")
      return
    
    try:
      init_no_config(categories, difficulties, port, config_only)
    except ValueError as e:
      print(f"[bright_red]{e}[/bright_red]")
      return
    else:
      print("[bright_green]Initialized CTF repo with specified config.[/bright_green]")