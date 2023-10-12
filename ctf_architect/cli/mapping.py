from __future__ import annotations

import typer
from rich import print
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ctf_architect.core.config import load_config, save_config
from ctf_architect.core.constants import APP_CMD_NAME
from ctf_architect.core.mappings import generate_port_mappings

mapping_app = typer.Typer()


def create_mapping_table(mappings: dict) -> Table:
  """
  Creates a rich table for the port mappings.
  """
  table = Table(title="Port Mappings")
  table.add_column("Service Name", header_style="bright_cyan", style="cyan")
  table.add_column("Container Port", header_style="bright_green", style="green")
  table.add_column("Host Port", header_style="bright_green", style="green")

  for service_name, port_mapping in mappings.items():
    table.add_row(service_name, port_mapping["from_port"], port_mapping["to_port"])

  return table


@mapping_app.callback()
def callback():
  """
  Commands to manage port mappings for challenges
  """


@mapping_app.command("generate")
def generate():
  """
  Generates the port mappings for challenges.
  """
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return
  
  mapping = generate_port_mappings()

  # Print and display the mappings in a table
  table = create_mapping_table(mapping)

  print(table)

  # Ask for confirmation to save the mappings
  if not Confirm.ask("Save port mappings to ctf_config.yaml?"):
    return

  config.port_mappings = mapping
  save_config(config)

  print("[green]Port mappings saved successfully.")


@mapping_app.command("show")
def show():
  # Show port mappings
  try:
    config = load_config()
  except FileNotFoundError:
    print(f"[bright_red]Challenge repo not found, are you in the correct directory? If so, please run `{APP_CMD_NAME} init` first.")
    return
  
  if config.port_mappings is None:
    print("[bright_red]No port mappings found.[/bright_red]")
    return
  
  table = create_mapping_table(config.port_mappings)

  print(table)