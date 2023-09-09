"""
A cli to create challenges and export them as a zip file.
"""

from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ctf_architect.chall_architect.create import create_challenge
from ctf_architect.chall_architect.utils import is_valid_service_folder, get_config


try:
  import ctypes
  # Make it not blurry on windows
  ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
  pass


# This is to fix a bug on vscode's terminal where the filedialog window will not show up
_root = tk.Tk()
_root.withdraw()
_root.call('wm', 'attributes', '.', '-topmost', True)


app = typer.Typer()


console = Console()


def prompt(message: str, allow_empty: bool = False, method = Prompt.ask, **kwargs) -> str:
  """
  Prompts the user for input.
  """
  if not allow_empty:
    while True:
      res = method(message, **kwargs)
      if res != "":
        return res
      else:
        console.print("[bright_red]This field cannot be empty.[/bright_red]")
  else:
    return method(message)
  

def get_ctf_config():
  """
  Prompts the user for the ctf config.
  """
  console.rule(":gear: [bold yellow]CTF Config[/] :gear:")

  while True:

    console.print("[cyan]Please select the CTF config file.[/cyan]")
    time.sleep(1)

    config_file = askopenfilename(title="Please select the ctf config", filetypes=[("YAML", "*.yaml")])

    if config_file == "":
      # User cancelled, abort
      console.print("[bright_red]No file selected, aborting...[/bright_red]")
      return None
  
    try:
      config = get_config(config_file)
    except Exception as e:
      console.print(f"[bright_red]Error loading config file: {e}[/bright_red]")
      return None
    
    # Print config in a panel
    config_string = f"[cyan][bold]Categories:[/bold]"
    for category in config.categories:
      config_string += f"\n- {category.capitalize()}"

    config_string += f"\n\n[bold]Difficulties:[/bold]"
    for difficulty in config.difficulties:
      config_string += f"\n- {difficulty['name'].capitalize()} ({difficulty['value']})"
    config_string += "[/cyan]"

    config_name = config.name if config.name is not None else "Unnamed"

    console.print(Panel(
      config_string,
      border_style="green",
      title=f"[bright_yellow]{config_name} CTF Config[/bright_yellow]"
    ))

    if Confirm.ask("[cyan]Is this the correct config?[/]"):
      return config
    
    # Add spacing
    console.print()
  

def get_solution_files():
  """
  Prompts the user for the solution files.
  """
  console.rule(":file_folder: [bold yellow]Please select the solution files for the challenge.[/] :file_folder:")

  time.sleep(1)

  return askopenfilenames(title="Please select the solution files")


def get_flags() -> list[dict[str, str | bool]]:
  """
  Prompts the user for the flags.
  """
  console.rule(":triangular_flag: [bold yellow]Challenge Flags[/] :triangular_flag:")

  flags = []
  while True:
    regex = Confirm.ask(":triangular_flag: [cyan]Is the flag a regex flag?[/]")
    flag = prompt(":triangular_flag: [cyan]Please enter the flag[/]")
    flags.append({
      "flag": flag,
      "regex": regex
    })

    if not Confirm.ask("[cyan]Do you want to add another flag?[/]"):
      break

    # Add spacing between the flags
    console.print()

  return flags


def get_hints() -> list[dict[str, str | int | list[int]]] | None:
  """
  Prompts the user for the hints.
  """
  console.rule(":light_bulb: [bold yellow]Challenge Hints[/] :light_bulb:")

  has_hints = Confirm.ask(":light_bulb: [cyan]Does the challenge have hints?[/]")
  if has_hints:
    hints = []

    # Add spacing
    console.print()

    while True:
      hint_description = prompt(":light_bulb: [cyan]Please enter the hint description[/]")
      cost = prompt(":light_bulb: [cyan]Please enter the hint cost[/]", method=IntPrompt.ask)
      
      hint_req = None
      if len(hints) > 0:
        if Confirm.ask(":light_bulb: [cyan]Do you want to add a hint requirement?[/]"):
          # console.print the following hints in a list, with an index starting at 0
          console.print("\n[green]Hints:[/green]")
          console.print("\n".join([
            f"[green]{i}. {hint['description']} ({hint['cost']})[/]" 
            for i, hint in enumerate(hints)
          ]))

          valid = False

          while not valid:
            hint_req = prompt(":light_bulb: [cyan]Please enter the hint requirements (comma separated)[/]")
            hint_req = [int(i) for i in hint_req.split(",")]
            # Check if the requirements are valid
            for requirement in hint_req:
              if requirement >= len(hints):
                console.print("[bright_red]Invalid hint requirement.[/bright_red]")
                break
            else:
              valid = True

      hints.append({
        "description": hint_description,
        "cost": cost,
        "requirements": hint_req
      })

      if not Confirm.ask(":light_bulb: [cyan]Do you want to add another hint?[/]"):
        break

      # Add spacing between the hints
      console.print()

    return hints
  else:
    return None
  

def get_files() -> list[Path] | None:
  """
  Prompts the user for the files.
  """
  console.rule(":file_folder: [bold yellow]Challenge Files[/] :file_folder:")

  has_files = Confirm.ask("[cyan]Are there any files that should be given to participants for this challenge?[/]")
  if has_files:
    return askopenfilenames(title="Please select the challenge files")
  else:
    return None
  

def get_requirements() -> list[str] | None:
  """
  Prompts the user for the requirements.
  """
  console.rule(":triangular_flag: [bold yellow]Challenge Requirements[/] :triangular_flag:")

  has_requirements = Confirm.ask("[cyan]Do any challenges need to be solved before this challenge?[/]")
  if has_requirements:
    requirements = []
    while True:
      requirement = prompt("[cyan]Please enter the challenge name of the requirement (case-insensitive)[/]")
      requirements.append(requirement)
      if not Confirm.ask("[cyan]Do you want to add another requirement?[/]"):
        break

      # Add spacing between the requirements
      console.print()
  else:
    requirements = None
  
  return requirements
  



@app.command()
def create_challenge_cli():
  """
  Creates a challenge folder in the current directory.
  """

  config = get_ctf_config()

  if config is None:
    return
  
  categories = config.categories
  difficulties = config.diff_names

  try:
    console.rule(":rocket: [bold yellow]Challenge Details[/] :rocket:")

    name = prompt(":rocket: [cyan][1/6] Please enter the challenge name (case-insensitive)[/]")

    description = prompt("\n:rocket: [cyan][2/6] Please enter the challenge description (case-sensitive)[/]")

    # Print the categories in a list, with an index starting at 1
    console.print("\n[bright_yellow]Categories:[/]")
    for i, category in enumerate(categories):
      console.print(f"[bright_yellow]{i + 1}. {category.capitalize()}[/]")

    while True:
      category = prompt(f"\n:rocket: [cyan][3/6] Please choose the challenge category \[1-{len(categories)}][/]", method=IntPrompt.ask)
      if 1 > category > len(categories):
        console.print("[bright_red]Invalid category.[/bright_red]\n")
      else:
        category = categories[category - 1].capitalize()
        break

    console.print(f"[green]Category selected: {category}[/green]\n")


    # Print the difficulties in a list, with an index starting at 1
    console.print("[bright_yellow]Difficulties:[/]")
    for i, difficulty in enumerate(difficulties):
      console.print(f"[bright_yellow]{i + 1}. {difficulty.capitalize()}[/]")

    while True:
      difficulty = prompt(f"\n:rocket: [cyan][4/6] Please choose the challenge difficulty \[1-{len(difficulties)}][/]", method=IntPrompt.ask)
      if 1 > difficulty > len(difficulties):
        console.print("[bright_red]Invalid difficulty.[/bright_red]\n")
      else:
        difficulty = difficulties[difficulty - 1].capitalize()
        break

    console.print(f"[green]Difficulty selected: {difficulty}[/green]\n")

    author = prompt("\n:rocket: [cyan][5/6] Please enter your name (case-sensitive)[/]")

    discord = prompt("\n:rocket: [cyan][6/6] Please enter your discord username (So we can contact you if your challenge breaks)[/]")

    solution_files = get_solution_files()
    if solution_files == "":
      # User cancelled, abort
      console.print("[bright_red]No files selected, aborting...[/bright_red]")
      return
    
    elif solution_files is not None:
      solution_files = [Path(file) for file in solution_files]

      console.print("[green]Solution files selected: [/green]")
      for file in solution_files:
        console.print(f"[light_green]- {file}[/light_green]")


    flags = get_flags()

    hints = get_hints()

    requirements = get_requirements()

    files = get_files()
    if files == "":
      # User cancelled, abort
      console.print("[bright_red]No files selected, aborting...[/bright_red]")
      return
    
    elif files is not None:
      files = [Path(file) for file in files]

      console.print("[green]Files selected: [/green]")
      for file in files:
        console.print(f"[light_green]- {file}[/light_green]")


    console.rule(":file_folder: [bold yellow]Challenge Services[/] :file_folder:")
    has_serivices = Confirm.ask("[cyan]Does the challenge require hosting?[/]")
    if has_serivices:
      services = []

      # Add spacing
      console.print()

      while True:
        service_name = prompt("[cyan]Please enter the service name (this will be the name of the docker container)[/]")
        service_path = askdirectory(title="Please select the folder containing the dockerfile")

        if service_path == "":
          # User cancelled, abort
          console.print("[bright_red]No directory selected, aborting...[/bright_red]")
          return

        if not is_valid_service_folder(service_path):
          console.print("[bright_red]Invalid service folder, aborting...[/bright_red]")
          return

        service_port = prompt("[cyan]Please enter the port exposed by the service[/]", method=IntPrompt.ask)
        services.append({
          "name": service_name,
          "path": service_path,
          "port": service_port
        })
        if not Confirm.ask("[cyan]Do you want to add another service?[/]"):
          break
    else:
      services = None


    # console.print the challenge details in a panel
    info_string = f"[cyan][bold]Name:[/bold] {name}\n"
    info_string += f"[bold]Description:[/bold] {description}\n"
    info_string += f"[bold]Category:[/bold] {category}\n"
    info_string += f"[bold]Difficulty:[/bold] {difficulty}\n"
    info_string += f"[bold]Author:[/bold] {author}\n"
    info_string += f"[bold]Discord:[/bold] {discord}\n\n"

    info_string += f"[bold]Solution Files:[/bold]\n"
    for file in solution_files:
      info_string += f"- {file.as_posix()}\n"
    info_string += "\n"

    info_string += f"[bold]Flags:[/bold] {', '.join([flag['flag'] for flag in flags])}\n\n"

    info_string += f"[bold]Hints:[/bold] {hints}\n\n"

    info_string += f"[bold]Files:[/bold]\n"
    if files is not None:
      for file in files:
        info_string += f"- {file.as_posix()}\n"
    else:
      info_string += "None\n"
    info_string += "\n"

    info_string += f"[bold]Requirements:[/bold] {requirements}\n\n"
    info_string += f"[bold]Services:[/bold] {services}[/cyan]"


    console.print(Panel(
      info_string,
      border_style="green",
      title="[bright_yellow]Challenge Details[/bright_yellow]"
    ))


    # Confirm that the user wants to create the challenge
    if not Confirm.ask("[cyan]Do you want to create the challenge?[/]"):
      console.print("[bright_red]Aborting...[/bright_red]")
      return


    challenge_path = create_challenge(
      name=name,
      description=description,
      difficulty=difficulty,
      category=category,
      author=author,
      discord=discord,
      solution_files=solution_files,
      flags=flags,
      hints=hints,
      files=files,
      requirements=requirements,
      services=services
    )

    console.print(f"[green]Successfully created challenge `{name}` at `{challenge_path.resolve()}`[/green]")

  except (KeyboardInterrupt, EOFError):
    console.print("[bright_red]Aborting...[/bright_red]")
    return
  except Exception as e:
    # This should not happen
    console.print(f"[bright_red]An unexpected error occurred: {e}[/bright_red]")
    return