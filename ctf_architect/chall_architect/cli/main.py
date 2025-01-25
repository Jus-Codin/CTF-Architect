from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.panel import Panel

from rich.tree import Tree

from ctf_architect._console import console
from ctf_architect.chall_architect.core.challenge import create_challenge
from ctf_architect.chall_architect.core.compose import create_challenge_compose_file
from ctf_architect.chall_architect.core.prompts import (
    ask_challenge_author,
    ask_challenge_category,
    ask_challenge_description,
    ask_challenge_difficulty,
    ask_challenge_extras,
    ask_challenge_files,
    ask_challenge_name,
    ask_challenge_requirements,
    ask_ctf_config,
    ask_flags,
    ask_folder_name,
    ask_hints,
    ask_services,
    ask_solution_files,
    ask_source_files,
    confirm,
)
from ctf_architect.chall_architect.core.utils import init_gui
from ctf_architect.core.challenge import is_challenge_folder
from ctf_architect.core.lint import LintResult, Linter
from ctf_architect.core.lint.rules import SeverityLevel
from ctf_architect.core.models import Flag

app = typer.Typer()


@app.command("init")
def init(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
    config: Annotated[
        Path | None, typer.Option("-c", "--config", help="Path to the CTF config file")
    ] = None,
    name: Annotated[
        str | None, typer.Option("--name", help="Name of the challenge")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="Description of the challenge")
    ] = None,
    difficulty: Annotated[
        str | None, typer.Option("--difficulty", help="Difficulty of the challenge")
    ] = None,
    category: Annotated[
        str | None, typer.Option("--category", help="Category of the challenge")
    ] = None,
    author: Annotated[
        str | None, typer.Option("--author", help="Author of the challenge")
    ] = None,
    folder_name: Annotated[
        str | None, typer.Option("--folder-name", help="Name of the challenge folder")
    ] = None,
    requirements: Annotated[
        list[str] | None,
        typer.Option("--requirement", help="Requirements of the challenge"),
    ] = None,
    source_files: Annotated[
        list[Path] | None,
        typer.Option("--source", help="Source files of the challenge"),
    ] = None,
    solution_files: Annotated[
        list[Path] | None,
        typer.Option("--solution", help="Solution files of the challenge"),
    ] = None,
    local_files: Annotated[
        list[Path] | None,
        typer.Option("--local-file", help="Local files of the challenge"),
    ] = None,
    remote_files: Annotated[
        list[str] | None,
        typer.Option("--remote-file", help="Remote files of the challenge"),
    ] = None,
    flags: Annotated[
        list[str] | None, typer.Option("--flag", help="Flag of the challenge")
    ] = None,
):
    """Initialize a new challenge in the current directory"""
    if not no_gui:
        init_gui()

    ctf_config = ask_ctf_config(no_gui, config)

    name = name or ask_challenge_name()
    description = description or ask_challenge_description()
    difficulty = difficulty or ask_challenge_difficulty(ctf_config)
    category = category or ask_challenge_category(ctf_config)
    author = author or ask_challenge_author()

    if not ctf_config.extras:
        extras = None
    else:
        extras = ask_challenge_extras(ctf_config)

    files = []

    if local_files:
        files.extend(local_files)

    if remote_files:
        files.extend(remote_files)

    if not files:
        files = None

    if flags is not None:
        flags = [Flag(flag=flag) for flag in flags]

    # TODO: Find a better way to do this convoluted mess
    info_string = (
        f"[cyan]"
        f"[bright_cyan]Name:[/bright_cyan] {name}\n\n"
        f"[bright_cyan]Description:[/bright_cyan]\n"
        f"{description}\n\n"
        f"[bright_cyan]Difficulty:[/bright_cyan] {difficulty}\n"
        f"[bright_cyan]Category:[/bright_cyan] {category}\n"
        f"[bright_cyan]Author:[/bright_cyan] {author}\n"
    )

    if folder_name is None:
        info_string += "[bright_cyan]Folder Name:[/bright_cyan] Not Specified\n\n"
    else:
        info_string += f"[bright_cyan]Folder Name:[/bright_cyan] {folder_name}\n\n"

    if requirements is None:
        info_string += "[bright_cyan]Requirements:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Requirements:[/bright_cyan]\n"
        for requirement in requirements:
            info_string += f"  - {requirement}\n"
        info_string += "\n"

    if extras is None:
        info_string += "[bright_cyan]Extras:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Extras:[/bright_cyan]\n"
        for k, v in extras.items():
            info_string += f"  - [bright_cyan i]{k.capitalize()}:[/bright_cyan i] {v}\n"
        info_string += "\n"

    if source_files is None:
        info_string += "[bright_cyan]Source Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Source Files:[/bright_cyan]\n"
        for source_file in source_files:
            info_string += f"  - {source_file}\n"
        info_string += "\n"

    if solution_files is None:
        info_string += "[bright_cyan]Solution Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Solution Files:[/bright_cyan]\n"
        for solution_file in solution_files:
            info_string += f"  - {solution_file}\n"
        info_string += "\n"

    if files is None:
        info_string += "[bright_cyan]Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Files:[/bright_cyan]\n"
        for file in files:
            if isinstance(file, Path):
                info_string += f"  - {file}\n"
            else:
                info_string += f"  - [u blue link={file}]{file}[/u blue link]\n"
        info_string += "\n"

    if flags is None:
        info_string += "[bright_cyan]Flags:[/bright_cyan] None"
    else:
        info_string += "[bright_cyan]Flags:[/bright_cyan]\n"
        for i, flag in enumerate(flags, start=1):
            info_string += f"  [bright_cyan i]Flag {i}:[/bright_cyan i]\n"
            info_string += f"    [bright_cyan u]Content:[/bright_cyan u] {flag.flag}\n"
            info_string += f"    [bright_cyan u]Type:[/bright_cyan u] {'Regex' if flag.regex else 'Static'}\n"
            info_string += f"    [bright_cyan u]Case Sensitive:[/bright_cyan u] {flag.case_sensitive}\n"

    console.print(
        Panel(
            info_string,
            title="[bold yellow]Challenge Details[/bold yellow]",
            border_style="blue",
        )
    )

    if not confirm("Do you want to create the challenge?"):
        console.print("Aborting...", style="red")
        return

    _, challenge_path = create_challenge(
        name=name,
        description=description,
        difficulty=difficulty,
        category=category,
        author=author,
        folder_name=folder_name,
        source_files=source_files,
        solution_files=solution_files,
        files=files,
        requirements=requirements,
        extras=extras,
        flags=flags,
    )

    console.print(f'Challenge created at "{challenge_path.resolve()}"', style="green")


@app.command("package")
def package(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
    config: Annotated[
        Path | None, typer.Option("-c", "--config", help="Path to the CTF config file")
    ] = None,
    name: Annotated[
        str | None, typer.Option("--name", help="Name of the challenge")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="Description of the challenge")
    ] = None,
    difficulty: Annotated[
        str | None, typer.Option("--difficulty", help="Difficulty of the challenge")
    ] = None,
    category: Annotated[
        str | None, typer.Option("--category", help="Category of the challenge")
    ] = None,
    author: Annotated[
        str | None, typer.Option("--author", help="Author of the challenge")
    ] = None,
    folder_name: Annotated[
        str | None, typer.Option("--folder-name", help="Name of the challenge folder")
    ] = None,
    requirements: Annotated[
        list[str] | None,
        typer.Option("--requirement", help="Requirements of the challenge"),
    ] = None,
    source_files: Annotated[
        list[Path] | None,
        typer.Option("--source", help="Source files of the challenge"),
    ] = None,
    solution_files: Annotated[
        list[Path] | None,
        typer.Option("--solution", help="Solution files of the challenge"),
    ] = None,
    local_files: Annotated[
        list[Path] | None,
        typer.Option("--local-file", help="Local files of the challenge"),
    ] = None,
    remote_files: Annotated[
        list[str] | None,
        typer.Option("--remote-file", help="Remote files of the challenge"),
    ] = None,
    flags: Annotated[
        list[str] | None, typer.Option("--flag", help="Flag of the challenge")
    ] = None,
    hints: Annotated[
        list[str] | None, typer.Option("--hint", help="Hints of the challenge")
    ] = None,
    service_paths: Annotated[
        list[Path] | None,
        typer.Option("--service-path", help="Paths of services for the challenge"),
    ] = None,
    create_compose: Annotated[
        bool | None,
        typer.Option("--create-compose", help="Create a docker-compose file"),
    ] = None,
):
    """
    Package a challenge into a folder in the current directory
    """

    if not no_gui:
        init_gui()

    ctf_config = ask_ctf_config(no_gui, config)

    name = name or ask_challenge_name()
    description = description or ask_challenge_description()
    difficulty = difficulty or ask_challenge_difficulty(ctf_config)
    category = category or ask_challenge_category(ctf_config)
    author = author or ask_challenge_author()

    if not ctf_config.extras:
        extras = None
    else:
        extras = ask_challenge_extras(ctf_config)

    if folder_name is None and confirm(
        "Do you want to specify a different folder name?"
    ):
        folder_name = ask_folder_name(name)

    console.print()

    if requirements is None and confirm(
        "Do you want to specify requirements for the challenge?"
    ):
        requirements = ask_challenge_requirements()

    console.print()

    if source_files is None and confirm(
        "Do have any source files for debugging to specify?"
    ):
        source_files = ask_source_files(no_gui)

    console.print()

    if not solution_files and confirm(
        "Do you have any solution files (writeups, solve scripts etc.) for the challenge?"
    ):
        solution_files = ask_solution_files(no_gui)

    console.print()

    files = []

    if local_files:
        files.extend(local_files)

    if remote_files:
        files.extend(remote_files)

    if not files:
        if confirm("Do you have any files to give to challenge attempters?"):
            files = ask_challenge_files(no_gui)
        else:
            files = None
        console.print()

    if flags is not None:
        flags = [Flag(flag=flag) for flag in flags]
    else:
        if confirm("Do you want to specify a flag for the challenge?"):
            flags = ask_flags()
        console.print()

    if hints is None and not confirm("Do you want to specify hints for the challenge?"):
        hints = None
    else:
        hints = ask_hints(hints)

    console.print()

    if service_paths is None and not confirm(
        "Do you want to specify services for the challenge?"
    ):
        services = None
        create_compose = False
    else:
        services = ask_services(no_gui, service_paths)

    console.print()

    if services is None or len(services) > 0:
        if create_compose is None:
            create_compose = confirm(
                "Do you want to create a docker-compose file for the services?"
            )
    elif create_compose is None:
        create_compose = False
    else:
        console.print(
            ":warning: Cannot create a Compose file with no services specified, ignoring...",
            style="yellow",
        )
        create_compose = False

    # TODO: Find a better way to do this convoluted mess
    info_string = (
        f"[cyan]"
        f"[bright_cyan]Name:[/bright_cyan] {name}\n\n"
        f"[bright_cyan]Description:[/bright_cyan]\n"
        f"{description}\n\n"
        f"[bright_cyan]Difficulty:[/bright_cyan] {difficulty}\n"
        f"[bright_cyan]Category:[/bright_cyan] {category}\n"
        f"[bright_cyan]Author:[/bright_cyan] {author}\n"
    )

    if folder_name is None:
        info_string += "[bright_cyan]Folder Name:[/bright_cyan] Not Specified\n\n"
    else:
        info_string += f"[bright_cyan]Folder Name:[/bright_cyan] {folder_name}\n\n"

    if requirements is None:
        info_string += "[bright_cyan]Requirements:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Requirements:[/bright_cyan]\n"
        for requirement in requirements:
            info_string += f"  - {requirement}\n"
        info_string += "\n"

    if extras is None:
        info_string += "[bright_cyan]Extras:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Extras:[/bright_cyan]\n"
        for k, v in extras.items():
            info_string += f"  - [bright_cyan i]{k.capitalize()}:[/bright_cyan i] {v}\n"
        info_string += "\n"

    if source_files is None:
        info_string += "[bright_cyan]Source Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Source Files:[/bright_cyan]\n"
        for source_file in source_files:
            info_string += f"  - {source_file}\n"
        info_string += "\n"

    if solution_files is None:
        info_string += "[bright_cyan]Solution Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Solution Files:[/bright_cyan]\n"
        for solution_file in solution_files:
            info_string += f"  - {solution_file}\n"
        info_string += "\n"

    if files is None:
        info_string += "[bright_cyan]Files:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Files:[/bright_cyan]\n"
        for file in files:
            if isinstance(file, Path):
                info_string += f"  - {file}\n"
            else:
                info_string += f"  - [u blue link={file}]{file}[/u blue link]\n"
        info_string += "\n"

    if flags is None:
        info_string += "[bright_cyan]Flags:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Flags:[/bright_cyan]\n"
        for i, flag in enumerate(flags, start=1):
            info_string += f"  [bright_cyan i]Flag {i}:[/bright_cyan i]\n"
            info_string += f"    [bright_cyan u]Content:[/bright_cyan u] {flag.flag}\n"
            info_string += f"    [bright_cyan u]Type:[/bright_cyan u] {'Regex' if flag.regex else 'Static'}\n"
            info_string += f"    [bright_cyan u]Case Sensitive:[/bright_cyan u] {flag.case_sensitive}\n"
        info_string += "\n"

    if hints is None:
        info_string += "[bright_cyan]Hints:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Hints:[/bright_cyan]\n"
        for i, hint in enumerate(hints, start=1):
            info_string += f"  [bright_cyan i]Hint {i}:[/bright_cyan i]\n"
            info_string += (
                f"    [bright_cyan u]Content:[/bright_cyan u] {hint.content}\n"
            )
            info_string += f"    [bright_cyan u]Cost:[/bright_cyan u] {hint.cost}\n"
        info_string += "\n"

    if services is None:
        info_string += "[bright_cyan]Services:[/bright_cyan] None\n\n"
    else:
        info_string += "[bright_cyan]Services:[/bright_cyan]\n"
        for i, service in enumerate(services, start=1):
            info_string += f"  [bright_cyan i]Service {i}:[/bright_cyan i]\n"
            info_string += f"    [bright_cyan u]Name:[/bright_cyan u] {service.name}\n"
            info_string += f"    [bright_cyan u]Type:[/bright_cyan u] {service.type.capitalize()}\n"
            info_string += f"    [bright_cyan u]Path:[/bright_cyan u] {service.path}\n"
            info_string += f"    [bright_cyan u]Ports:[/bright_cyan u] {', '.join(service.ports_list)}\n"
        info_string += "\n"

    info_string += f"[bright_cyan]Create Docker Compose:[/bright_cyan] {create_compose}"

    console.print(
        Panel(
            info_string,
            title="[bold yellow]Challenge Details[/bold yellow]",
            border_style="blue",
        )
    )

    if not confirm("Do you want to create the challenge?"):
        console.print("Aborting...", style="red")
        return

    challenge, challenge_path = create_challenge(
        name=name,
        description=description,
        difficulty=difficulty,
        category=category,
        author=author,
        folder_name=folder_name,
        source_files=source_files,
        solution_files=solution_files,
        files=files,
        requirements=requirements,
        extras=extras,
        flags=flags,
        hints=hints,
        services=services,
    )

    if create_compose:
        try:
            create_challenge_compose_file(challenge)
        except Exception as e:
            console.print(f"Failed to create Docker Compose file: {e}", style="red")

    console.print(f'Challenge created at "{challenge_path.resolve()}"', style="green")


@app.command("lint")
def lint(
    no_gui: Annotated[
        bool, typer.Option("--no-gui", help="Don't use the GUI to create the challenge")
    ] = False,
    config: Annotated[
        Path | None, typer.Option("-c", "--config", help="Path to the CTF config file")
    ] = None,
    no_config_prompt: Annotated[
        bool,
        typer.Option(
            "--no-config-prompt",
            "-n",
            help="Don't prompt the user to create a CTF config file.",
        ),
    ] = False,
    ignore: Annotated[
        list[str] | None,
        typer.Option(
            "--ignore",
            "-i",
            help="Ignore specific rules by their codes.",
        ),
    ] = None,
    level: Annotated[
        str,
        typer.Option(
            "--level",
            "-l",
            help="Set the minimum severity level to lint for.",
        ),
    ] = "error",
    hide_non_violations: Annotated[
        bool,
        typer.Option(
            "--hide-non-violations",
            "-h",
            help="Hide non-violations from the output.",
        ),
    ] = False,
):
    _cwd = Path.cwd()

    if not is_challenge_folder(_cwd):
        console.print(
            "Not a valid challenge repo. Are you in the right directory?", style="red"
        )
        return

    if config is None and not no_config_prompt:
        if not no_gui:
            init_gui()

        ctf_config = ask_ctf_config(no_gui, config)
    else:
        console.print(
            ":warning:  Warning: no CTF config is provided, some rules will be unable to be checked.",
            style="yellow",
        )
        ctf_config = None

    match level.lower():
        case "info":
            level = SeverityLevel.INFO
        case "warning":
            level = SeverityLevel.WARNING
        case "error":
            level = SeverityLevel.ERROR
        case "fatal":
            level = SeverityLevel.FATAL
        case _:
            console.print(
                "Invalid severity level. Please choose from info, warning, error, or fatal.",
                style="bright_red",
            )
            return

    linter = Linter(ctf_config=ctf_config, level=level, ignore=ignore)

    result = linter.lint(_cwd)

    LEVEL_MAP = {
        SeverityLevel.FATAL: ("bright_magenta", "✕"),
        SeverityLevel.ERROR: ("bright_red", "✕"),
        SeverityLevel.WARNING: ("bright_yellow", "⚠"),
        SeverityLevel.INFO: ("bright_cyan", "🛈"),
    }

    num_violations = len(result["violations"])

    if num_violations == 0 and hide_non_violations:
        console.print("No violations found.", style="green")
        return

    # show_violations = num_violations > 0 and not hide_non_violations
    if num_violations > 0 and not hide_non_violations

    # if num_violations == 0:
    #     if hide_non_violations:
    #         console.print("No violations found.", style="green")
    #         return

    #     root_label = "Lint Result (all passed)"
    # else:
    #     root_label = f"Lint Result ({num_violations} violations)"

    # tree = Tree(root_label)
    # violation_node = tree.add("Violations")

    # for violation in result["violations"]: