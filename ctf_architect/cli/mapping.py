from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ctf_architect.core.mapping import (
    generate_port_mapping,
    load_port_mapping,
    save_port_mapping,
)
from ctf_architect.core.models import PortMapping

console = Console()


mapping_app = typer.Typer()


def create_mapping_table(mapping: dict[str, list[PortMapping]]) -> Table:
    table = Table(title="Port Mappings")
    table.add_column("Service Name", header_style="bright_cyan", style="cyan")
    table.add_column("Container Port", header_style="bright_green", style="green")
    table.add_column("Host Port", header_style="bright_green", style="green")

    for service_name, port_mapping in mapping.items():
        first = True
        for port in port_mapping:
            if first:
                table.add_row(service_name, str(port.from_port), str(port.to_port))
                first = False
            else:
                table.add_row("-", str(port.from_port), str(port.to_port))

    return table


@mapping_app.callback()
def callback():
    """
    Commands to manage port mappings for challenge services
    """


@mapping_app.command("generate")
def generate():
    """
    Generates port mappings for challenge services
    """
    try:
        mapping = generate_port_mapping()
    except FileNotFoundError:
        console.print(
            "Could not find CTF config file. Are you in the right directory?",
            style="bright_red",
        )
        return
    except Exception as e:
        console.print(f"Error generating port mapping: {e}", style="bright_red")
        return

    table = create_mapping_table(mapping)
    console.print(table)

    if not Confirm.ask("Do you want to save the port mapping?"):
        return

    save_port_mapping(mapping)
    console.print("Port mapping saved successfully", style="green")


@mapping_app.command("show")
def show():
    """
    Show the current port mappings
    """
    try:
        mapping = load_port_mapping()
    except FileNotFoundError:
        console.print(
            "Could not find port mapping file. Have you generated the port mapping?",
            style="bright_red",
        )
        return
    except Exception as e:
        console.print(f"Error loading port mapping: {e}", style="bright_red")
        return

    table = create_mapping_table(mapping.mapping)
    console.print(table)
