from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from types import EllipsisType

from rich.panel import Panel
from rich.table import Table

from ctf_architect.core.initialize import (
    ExtraFieldDict,
    FlagDict,
    HintDict,
    ServiceDict,
)
from ctf_architect.models.challenge import Flag, Hint, Service
from ctf_architect.models.ctf_config import ExtraField
from ctf_architect.models.port_mapping import PortMapping


def create_repo_config_panels(
    name: str,
    flag_format: str | None,
    starting_port: int | None,
    categories: list[str],
    difficulties: list[str],
    extras: list[ExtraField] | list[ExtraFieldDict] | None,
) -> Iterable[Panel]:
    _panels = []

    ctf_config_panel = Panel(
        (
            f" CTF Name: {name}\n"
            f" Flag Format: {flag_format if flag_format else 'None'}\n"
            f" Starting Port: {starting_port if starting_port else 'None'}"
        ),
        title="CTF Config",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(ctf_config_panel)

    categories_panel = Panel(
        "\n".join([f"  - {category.capitalize()}" for category in categories]),
        title="Categories",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(categories_panel)

    difficulties_panel = Panel(
        "\n".join([f"  - {difficulty.capitalize()}" for difficulty in difficulties]),
        title="Difficulties",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(difficulties_panel)

    extras_panel = Panel(
        "\n".join(
            [
                f"  - {extra['name']} ({extra['type']})"
                if isinstance(extra, dict)
                else f"  - {extra.name} ({extra.type})"
                for extra in extras
            ]
        )
        if extras
        else "  - None",
        title="Extras",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(extras_panel)

    for panel in _panels:  # noqa: UP028
        yield panel


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


def create_chall_config_panels(
    author: str,
    category: str,
    description: str,
    difficulty: str,
    name: str,
    flags: list[Flag] | list[FlagDict],
    folder_name: str | None,
    dist_files: list[str | Path] | None,
    requirements: list[str] | None,
    extras: dict[str, str | int | float | bool] | None,
    hints: list[Hint] | list[HintDict] | None,
    services: list[Service] | list[ServiceDict] | None,
    source_files: list[Path] | None | EllipsisType = ...,
    solution_files: list[Path] | None | EllipsisType = ...,
) -> Iterable[Panel]:
    _panels = []

    chall_config_panel = Panel(
        (
            f" Name: {name}\n"
            f" Author: {author}\n"
            f" Category: {category.capitalize()}\n"
            f" Difficulty: {difficulty.capitalize()}\n"
            f" Description: {description}\n"
            f" Folder Name: {folder_name if folder_name else 'None'}"
        ),
        title=":gear: Challenge Config",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(chall_config_panel)

    requirements_panel = Panel(
        "\n".join([f"  - {requirement}" for requirement in requirements]) if requirements else "  - None",
        title=":gear: Requirements",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(requirements_panel)

    extras_panel = Panel(
        "\n".join([f"  - {key}: {value}" for key, value in extras.items()]) if extras else "  - None",
        title=":package: Extras",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(extras_panel)

    hints_panel = Panel(
        "\n".join(
            [
                f"  - {hint['content']} ({hint['cost']} points)"
                if isinstance(hint, dict)
                else f"  - {hint.content} ({hint.cost} points)"
                for hint in hints
            ]
        )
        if hints
        else "  - None",
        title=":bulb: Hints",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(hints_panel)

    dist_files_panel = Panel(
        "\n".join([f"  - {file}" for file in dist_files]) if dist_files else "  - None",
        title=":file_folder: Dist Files",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(dist_files_panel)

    if source_files != ...:
        source_files_panel = Panel(
            "\n".join([f"  - {file}" for file in source_files]) if source_files else "  - None",
            title=":file_folder: Source Files",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
        _panels.append(source_files_panel)

    if solution_files != ...:
        solution_files_panel = Panel(
            "\n".join([f"  - {file}" for file in solution_files]) if solution_files else "  - None",
            title=":file_folder: Solution Files",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
        _panels.append(solution_files_panel)

    flags_table = Table()
    flags_table.add_column("Flag", header_style="bright_cyan", style="cyan")
    flags_table.add_column("Type", header_style="bright_green", style="green")
    flags_table.add_column("Case-Insensitive", header_style="bright_green", style="green")

    for flag in flags:
        if isinstance(flag, dict):
            flags_table.add_row(
                flag["flag"],
                "regex" if flag["regex"] else "static",
                str(flag["case_insensitive"]),
            )
        else:
            flags_table.add_row(
                flag.flag,
                "regex" if flag.regex else "static",
                str(flag.case_insensitive),
            )

    flags_panel = Panel(
        flags_table,
        title=":triangular_flag: Flags",
        title_align="left",
        style="ctfa.info",
        border_style="green",
    )
    _panels.append(flags_panel)

    if services is None:
        service_panel = Panel(
            "  - None",
            title=":computer: Services",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
    else:
        services_table = Table()
        services_table.add_column("Service Name", header_style="bright_cyan", style="cyan")
        services_table.add_column("Path", header_style="bright_green", style="green")
        services_table.add_column("Ports", header_style="bright_green", style="green")
        services_table.add_column("Type", header_style="bright_green", style="green")

        for service in services:
            if isinstance(service, dict):
                if "port" in service:
                    _ports = [service["port"]]
                elif "ports" in service:
                    _ports = service["ports"]
                else:
                    _ports = []

                services_table.add_row(
                    service["name"],
                    service["path"].as_posix(),
                    ", ".join(str(p) for p in _ports),
                    service["type"],
                )

            else:
                services_table.add_row(
                    service.name,
                    service.path.as_posix(),
                    ", ".join(str(p) for p in service.ports_list),
                    service.type,
                )

        service_panel = Panel(
            services_table,
            title=":computer: Services",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
    _panels.append(service_panel)

    for panel in _panels:  # noqa: UP028
        yield panel
