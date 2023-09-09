from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ctf_architect.cli.challenge import challenge_app
from ctf_architect.cli.stats import stats_app
from ctf_architect.core.initialize import init_no_config, init_with_config

console = Console()


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
    console.print("[bright_red]ctf_config.yaml already exists.[/bright_red]")
    return
  
  # Check if there is a ctf_config.yaml in the current directory, if so, use that config
  # Otherwise, use the config specified in the command line arguments
  if Path("ctf_config.yaml").exists():
    try:
      init_with_config()
    except ValueError as e:
      console.print(f"[bright_red]{e}[/bright_red]")
      return
    else:
      console.print("[bright_green]Initialized CTF repo with the config in ctf_config.yaml.[/bright_green]")
  
  else:

    # Get the categories and difficulties from the user
    categories = []
    difficulties = []

    try:
      console.rule("[bold yellow]CTF Categories[/]")

      console.print("[bold cyan]Please enter the categories for your CTF. Enter an empty string to stop.[/]")

      while True:
        category = Prompt.ask("[cyan]Category name[/]", default="", show_default=False)
        if category == "":
          break
        categories.append(category.lower())

        console.print(f"\n[green]Category {category} added.[/]\n")

      if len(categories) == 0:
        console.print("[bright_red]Please specify at least one category.[/bright_red]")
        return
      else:
        console.print(f"\n[bold green]Categories:[/]")
        for category in categories:
          console.print(f"[green] - {category}[/]")


      console.rule("[bold yellow]CTF Difficulties[/]")

      console.print("\n[bold cyan]Please enter the difficulties for your CTF. Enter an empty string to stop.[/]")

      while True:
        name = Prompt.ask("[cyan]Difficulty name[/]", default="", show_default=False)
        if name == "":
          break
        value = IntPrompt.ask("[cyan]Difficulty value[/]", default=500)
        difficulties.append({
          "name": name.lower(),
          "value": value
        })

        console.print(f"\n[green]Difficulty {name} added. ({value} points)[/]\n")

      if len(difficulties) == 0:
        console.print("[bright_red]Please specify at least one difficulty.[/bright_red]")
        return
      else:
        console.print(f"\n[bold green]Difficulties:[/]")
        for difficulty in difficulties:
          console.print(f"[green] - {difficulty['name']} ({difficulty['value']} points)[/]")
    except (KeyboardInterrupt, EOFError):
      console.print("\n[bright_red]Aborting...[/bright_red]")
      return


    # Show panel of categories and difficulties
    # If the user confirms, initialize the CTF repo
    
    config_text = ""
    config_text += "[bold cyan]Categories:[/]\n"
    for category in categories:
      config_text += f"[cyan] - {category}[/]\n"
    config_text += "\n"
    config_text += "[bold cyan]Difficulties:[/]\n"
    for difficulty in difficulties:
      config_text += f"[cyan] - {difficulty['name']} ({difficulty['value']} points)[/]\n"

    console.print(
      Panel(
        config_text,
        title="[bright_yellow]CTF Config[/bright_yellow]",
        border_style="green"
      )
    )

    if not Confirm.ask("[cyan]Is this correct?[/]"):
      console.print("[bright_red]Aborting...[/bright_red]")
      return

    
    try:
      init_no_config(categories, difficulties, port, config_only)
    except ValueError as e:
      console.print(f"[bright_red]{e}[/bright_red]")
      return
    else:
      console.print("[bright_green]Initialized CTF repo with specified config.[/bright_green]")