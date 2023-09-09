from __future__ import annotations

from pathlib import Path
import shutil

import typer
from rich import print
from rich.panel import Panel

from ctf_architect.core.challenge import add_challenge, find_challenge
from ctf_architect.core.config import load_config
from ctf_architect.core.constants import APP_CMD_NAME
from ctf_architect.core.stats import (update_category_readme,
                         update_root_readme)
from ctf_architect.core.unzip import unzip


def is_challenge_repo() -> bool:
  """
  Checks if the current working directory is a challenge repo.

  A challenge repo is considered valid if it has a ctf_config.yaml and a challenges folder.
  """
  return Path("ctf_config.yaml").exists() and Path("challenges").exists()


challenge_app = typer.Typer()


@challenge_app.callback()
def callback():
  """
  Commands to manage challenges.
  """


@challenge_app.command("import")
def challenge_import(
  path: str = typer.Option(default="./", help="Specify the path to the challenge zip files."),
  delete_on_error: bool = typer.Option(False, "--delete-on-error", "-d", help="Delete the challenge folder if an error occurs."),
  replace: bool = typer.Option(False, "--replace", "-r", help="Replace all existing challenges."),
  update_stats: bool = typer.Option(True, "--update-stats", "-u", help="Update the stats after importing.")
):
  """
  Imports challenges from zip files in the specified path.
  """
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return
  
  zip_path = Path(path)
  extracted_path = Path("extracted")

  if not zip_path.exists():
    print(f"[bright_red]Path `{zip_path}` does not exist.[/bright_red]")
    return
  
  success = 0
  unzip_failed = 0
  add_failed = 0

  for zip_file in zip_path.glob("*.zip"):
    try:
      # Unzip the file
      extracted = unzip(zip_file, extracted_path, delete=False)
    except Exception as e:
      print(f"[bright_red]Failed to unzip challenge `{zip_file.name}`:[/bright_red]")
      print(f"[bright_red]{e}[/bright_red]")
      unzip_failed += 1
      continue
    
    try:
      # Add the challenge
      add_challenge(extracted, replace=replace)
    except FileExistsError:
      # Prompt the user if they want to replace the challenge
      print(f"[bright_red]Challenge `{extracted.name}` already exists.[/bright_red]")
      if typer.confirm("Do you want to replace it?"):
        add_challenge(extracted, replace=True)
        print(f"[green]Successfully added challenge `{extracted.name}`[/green]")
        success += 1
      else:
        print(f"[bright_red]Skipping challenge `{extracted.name}`[/bright_red]")
        add_failed += 1
        continue
    except Exception as e:
      print(f"[bright_red]Failed to add challenge `{extracted.name}`:[/bright_red]")
      print(f"[bright_red]{e}[/bright_red]")
      # Delete the challenge folder if it exists
      if extracted.exists() and delete_on_error:
        shutil.rmtree(extracted)
      add_failed += 1
      continue
    else:
      print(f"[green]Successfully added challenge `{extracted.name}`[/green]")
      success += 1

  print(f"[green]Successfully imported {success} challenges[/green]")
  if unzip_failed > 0:
    print(f"[bright_red]Failed to unzip {unzip_failed} challenges[/bright_red]")
  if add_failed > 0:
    print(f"[bright_red]Failed to add {add_failed} challenges[/bright_red]")

  # Update the stats
  if update_stats and success > 0:
    for category in config.categories:
      update_category_readme(category)
    
    update_root_readme()

    print("[green]Repo READMEs updated successfully.")


@challenge_app.command("export")
def challenge_export(
  name: str = typer.Argument(..., help="The name of the challenge to export."),
  path: str = typer.Option("./", "--path", "-p", help="Specify the path to export the challenge to."),
  filename: str = typer.Option(None, "--filename", "-f", help="Specify the filename of the exported challenge."),
):
  """
  Exports the challenge as a zip file

  NOTE: For some reason if a directory is created where the zip file is supposed to be, admin privileges are required to delete the directory.
  """
  if not is_challenge_repo():
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return
  
  challenge = find_challenge(name)

  if challenge is None:
    print(f"[bright_red]Challenge `{name}` not found.[/bright_red]")
    return
  
  challenge_path = challenge[1]

  if filename is None:
    filename = challenge_path.name

  path = Path(path) / filename

  archive_path = shutil.make_archive(path, "zip", challenge_path)

  print(f"[green]Successfully exported challenge `{name}` to `{archive_path}`[/green]")


@challenge_app.command("info")
def challenge_info(name: str = typer.Argument(..., help="The name of the challenge to get info for.")):
  """
  Gets the info of a challenge.
  """
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return
  
  challenge = find_challenge(name)

  if challenge is None:
    print(f"[bright_red]Challenge `{name}` not found.[/bright_red]")
    return
  
  challenge_info, challenge_path = challenge

  info = (
    f"[bold]Name:[/] {challenge_info.name}\n"
    f"[bold]Description:[/] {challenge_info.description.strip()}\n\n"

    f"[bold]Difficulty:[/] {challenge_info.difficulty.capitalize()}\n"
    f"[bold]Category:[/] {challenge_info.category.capitalize()}\n"
    f"[bold]Author:[/] {challenge_info.author}\n"
    f"[bold]Discord:[/] {challenge_info.discord}\n"
  )

  if challenge_info.services is not None:
    info += "\n[bold]Services:[/]"
    for service in challenge_info.services:
      info += (
        f"\n - [bold]Name:[/] {service.name}\n"
        f" - [bold]Path:[/] {service.path}\n"
        # f" - [bold]Path:[/] {(challenge_path / service.path).resolve()}\n"
        f" - [bold]Port:[/] {service.port}\n"
      )

  print(Panel.fit(
    info,
    title=f"Challenge Info for {challenge_info.name}",
    border_style="bright_cyan",
    padding=(1, 2)
  ))