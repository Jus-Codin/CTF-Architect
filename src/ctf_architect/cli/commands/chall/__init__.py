from __future__ import annotations

import re
from pathlib import Path
from textwrap import shorten
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import ResolvedExistingDirectory, ResolvedExistingFile
from rich.panel import Panel
from rich.tree import Tree

from ctf_architect.cli.ui.components import create_chall_config_panels
from ctf_architect.cli.ui.console import console
from ctf_architect.cli.ui.prompts import (
    confirm,
    input_float,
    input_int,
    input_str,
    multi_select,
    multiline_input,
    select,
)
from ctf_architect.cli.utils import (
    ask_dist_files,
    ask_repo_config,
    ask_service_folder,
    ask_solution_files,
    ask_source_files,
    valid_chall_name,
)
from ctf_architect.cli.validators import (
    valid_chall_folder_name,
    valid_port,
    valid_service_name,
)
from ctf_architect.core.challenge import is_challenge_folder, load_chall_config, save_chall_config, save_chall_readme
from ctf_architect.core.initialize import init_chall
from ctf_architect.core.lint import lint_challenge
from ctf_architect.core.repo import load_repo_config
from ctf_architect.models.ctf_config import CTFConfig
from ctf_architect.models.lint import SeverityLevel

app = App(
    name="chall",
    group="Subcommands",
    help="Commands for creating and editing challenges.",
)


def _ask_and_create_chall(config: CTFConfig, target_dir: str | Path | None = None) -> None:
    # Challenge Name
    _must_specify_folder_name = False

    while True:
        name = input_str(":rocket: Enter the challenge name", allow_empty=False).execute()

        if not valid_chall_name(name):
            console.print(
                "Invalid challenge name, unable to create a valid folder name.",
                style="ctfa.warning",
            )

            _choice = select(
                choices=[
                    "Different challenge name",
                    "Specify folder name manually",
                    "Abort",
                ],
                prompt="What would you like to do?",
                return_index=True,
                prompt_suffix="",
            ).execute()

            if _choice == 0:
                continue
            elif _choice == 1:
                _must_specify_folder_name = True
                break
            elif _choice == 2:
                console.print("Aborting...", style="ctfa.error")
                return

        break

    console.print()  # Add spacing

    # Folder name
    if _must_specify_folder_name or confirm(":pencil: Would you like to specify the folder name manually?").execute():
        folder_name = input_str(
            ":rocket: Enter the challenge folder name",
            validator=valid_chall_folder_name,
        ).execute()
    else:
        folder_name = None

    console.print()  # Add spacing

    # Description
    description = multiline_input(":pencil: Enter the challenge description").execute()

    console.print()  # Add spacing

    # Category
    category = select(
        prompt=":label: Select the challenge category",
        choices=config.categories,
    ).execute()

    console.print()  # Add spacing

    # Difficulty
    difficulty = select(
        prompt=":bar_chart: Select the challenge difficulty",
        choices=config.difficulties,
    ).execute()

    console.print()  # Add spacing

    # Author
    author = input_str(":bust_in_silhouette: Enter the challenge author").execute()

    console.print()  # Add spacing

    # Tags
    extras = {}
    if config.extras is not None:
        for extra_field in config.extras:
            if not extra_field.required:
                if not confirm(
                    f"Would you like to provide the {extra_field.name} extra field? ({extra_field.description})"
                ):
                    continue

            if extra_field.type == "string":
                input_func = input_str
            elif extra_field.type == "integer":
                input_func = input_int
            elif extra_field.type == "float":
                input_func = input_float
            elif extra_field.type == "boolean":
                input_func = confirm
            else:
                console.print(
                    f'Unsupported extra field type "{extra_field.type}", skipping...',
                    style="ctfa.warning",
                )
                continue

            extras[extra_field.name] = input_func(extra_field.prompt).execute()

    console.print()  # Add spacing

    # Requirements
    if confirm("Would you like to specify the requirements for the challenge?").execute():
        requirements = []

        while True:
            requirement = input_str(":gear: Enter a requirement", allow_empty=False).execute()

            requirements.append(requirement)

            if not confirm("Do you want to add another requirement?").execute():
                break

            # Add spacing
            console.print()
    else:
        requirements = None

    console.print()  # Add spacing

    # Flags
    flags = []

    while True:
        _flag_type = select(
            prompt=":triangular_flag: Select the type of flag to add",
            choices=["Static", "Regex", "Finish"],
        ).execute()

        if _flag_type == "Finish":
            if not flags:
                console.print(":x: You must add at least one flag", style="ctfa.error")
                continue

            break

        _flag_case_insensitive = confirm("Is the flag case-insensitive?").execute()

        if _flag_type == "Static":
            while True:
                _flag_content = input_str(":triangular_flag: Enter the flag").execute()

                if config.flag_format is not None and not re.match(config.flag_format, _flag_content):
                    if not confirm(
                        "Flag does not match the expected format, are you sure you want to continue?"
                    ).execute():
                        console.print(
                            "Invalid flag format, please try again.",
                            style="ctfa.warning",
                        )
                        continue

                break

            flags.append(
                {
                    "flag": _flag_content,
                    "regex": False,
                    "case_insensitive": _flag_case_insensitive,
                }
            )
        elif _flag_type == "Regex":
            # TODO: Figure out how to validate regex
            _flag_content = input_str(":triangular_flag: Enter the flag regex").execute()

            flags.append(
                {
                    "flag": _flag_content,
                    "regex": True,
                    "case_insensitive": _flag_case_insensitive,
                }
            )

        if not confirm("Would you like to add another flag?").execute():
            break

        # Add spacing
        console.print()

    console.print()  # Add spacing

    # Hints
    if confirm(":bulb: Does the challenge have hints?").execute():
        hints = []

        while True:
            _hint_content = multiline_input(":bulb: Enter the hint", allow_empty=False).execute()
            _hint_cost = input_int(":moneybag: Enter the hint cost").execute()

            if hints and confirm(":lock: Does this hint require a previous hint to be unlocked?").execute():
                _hint_requirements = multi_select(
                    choices=[
                        shorten(
                            " ".join(hint["content"].splitlines()),
                            width=50,
                            placeholder="...",
                        )
                        for hint in hints
                    ],
                    prompt=":lock: Select the hints required to unlock this hint",
                    return_indexes=True,
                ).execute()
            else:
                _hint_requirements = None

            hints.append(
                {
                    "content": _hint_content,
                    "cost": _hint_cost,
                    "requirements": _hint_requirements,
                }
            )

            if not confirm("Would you like to add another hint?").execute():
                break

            # Add spacing
            console.print()

        if not hints:
            console.print(":warning: No hints provided.", style="ctfa.warning")
    else:
        hints = None

    console.print()  # Add spacing

    # Distributable files
    if confirm("Does the challenge have distributable files?").execute():
        dist_files = ask_dist_files()

        if not dist_files:
            dist_files = None
    else:
        dist_files = None

    console.print()  # Add spacing

    # Source files
    if confirm("Does the challenge have source files?").execute():
        source_files = ask_source_files()

        if not source_files:
            source_files = None

    else:
        source_files = None

    console.print()  # Add spacing

    # Solution files
    if confirm("Does the challenge have solution files?").execute():
        solution_files = ask_solution_files()

        if not solution_files:
            solution_files = None
    else:
        solution_files = None

    console.print()  # Add spacing

    # Services
    if confirm(":computer: Would you like to import a service into this challenge?").execute():
        services = []

        while True:
            _service_type = select(
                prompt=":computer: Select the service type",
                choices=["Web", "TCP", "SSH", "Secret", "Internal", "Finish"],
            ).execute()

            if _service_type == "Finish":
                break

            _service_name = input_str(":computer: Enter the service name", validator=valid_service_name).execute()

            if _service_type != "Internal" or confirm("Does the service have a port?").execute():
                _service_ports = []

                while True:
                    _service_port = input_int(":computer: Enter the service port", validator=valid_port).execute()

                    _service_ports.append(_service_port)

                    if not confirm("Would you like to add another port?").execute():
                        break
            else:
                _service_ports = None

            _service_path = ask_service_folder()

            if _service_path is None:
                console.print("Cancelled service creation...", style="ctfa.warning")
                continue

            services.append(
                {
                    "name": _service_name,
                    "ports": _service_ports,
                    "type": _service_type.lower(),  # type: ignore
                    "path": _service_path,
                }
            )

            if not confirm("Would you like to add another service?").execute():
                break

            # Add spacing
            console.print()

        if not services:
            console.print(":warning: No services provided.", style="ctfa.warning")
            services = None
    else:
        services = None

    # Add spacing
    console.print()

    for panel in create_chall_config_panels(
        name=name,
        folder_name=folder_name,
        description=description,
        category=category,  # type: ignore
        difficulty=difficulty,  # type: ignore
        author=author,
        requirements=requirements,
        extras=extras,
        flags=flags,
        hints=hints,
        dist_files=dist_files,
        source_files=source_files,
        solution_files=solution_files,
        services=services,
    ):
        console.print(panel)

    if confirm("Is the challenge configuration correct?").execute():
        init_chall(
            author=author,
            category=category,  # type: ignore
            description=description,
            difficulty=difficulty,  # type: ignore
            name=name,
            flags=flags,
            folder_name=folder_name,
            dist_files=dist_files,
            source_files=source_files,
            solution_files=solution_files,
            requirements=requirements,
            extras=extras,
            hints=hints,
            services=services,
            target_dir=target_dir,
        )

        console.print(
            ":sparkles: Challenge initialized successfully! :sparkles:",
            style="ctfa.success",
        )
    else:
        console.print("Aborting...", style="ctfa.error")
        return


@app.command(group="Initialization")
def init(
    *,
    config_path: Annotated[ResolvedExistingFile | None, Parameter(name=["--config", "-c"])] = None,
):
    """Initialize a new challenge repository."""
    # Load the repo config
    if config_path is None:
        config = ask_repo_config()

        if config is None:
            console.print("Aborting...", style="ctfa.error")
            return
    else:
        config = load_repo_config(config_path)

    # Add spacing
    console.print()

    _ask_and_create_chall(config, Path.cwd())


@app.command(group="Initialization")
def new(
    *,
    config_path: Annotated[ResolvedExistingFile | None, Parameter(name=["--config", "-c"])] = None,
):
    """Create a challenge in a new folder."""
    # Load the repo config
    if config_path is None:
        config = ask_repo_config()

        if config is None:
            console.print("Aborting...", style="ctfa.error")
            return
    else:
        config = load_repo_config(config_path)

    # Add spacing
    console.print()

    _ask_and_create_chall(config)


@app.command(group="Linting")
def lint(
    chall_path: Annotated[ResolvedExistingDirectory | None, Parameter(name=["--path", "-p"])] = None,
    ctf_config: Annotated[ResolvedExistingFile | None, Parameter(name=["--config", "-c"], negative="")] = None,
    *,
    level: Annotated[SeverityLevel, Parameter(name=["--level", "-l"])] = SeverityLevel.WARNING,
    ignore: Annotated[list[str] | None, Parameter(name=["--ignore", "-i"])] = None,
    show_passed: Annotated[bool, Parameter(name=["--show-passed", "-P"])] = False,
    show_ignored: Annotated[bool, Parameter(name=["--show-ignored", "-I"])] = False,
    show_skipped: Annotated[bool, Parameter(name=["--show-skipped", "-S"])] = False,
):
    """Lint the current challenge.

    Args:
        chall_path (ResolvedExistingDirectory, optional): The path to the challenge directory. If not specified, the current directory is used.
        ctf_config (ResolvedExistingFile, optional): The path to the CTF repo config file.
        level (SeverityLevel, optional): Minimum severity level to lint for. Defaults to SeverityLevel.WARNING.
        ignore (list[str], optional): List of rule codes to ignore. Defaults to None.
        show_passed (bool, optional): Whether to show passed rules. Defaults to False.
        show_ignored (bool, optional): Whether to show ignored rules. Defaults to False.
        show_skipped (bool, optional): Whether to show skipped rules. Defaults to False.
    """
    if chall_path is None:
        chall_path = Path.cwd()

    if not is_challenge_folder(chall_path):
        console.print(":x: Specified path is not a challenge folder.", style="ctfa.error")
        return

    if ctf_config is None:
        if confirm("Would you like to select a CTF config file?").execute():
            config = ask_repo_config()

            if config is None:
                console.print("Aborting...", style="ctfa.error")
                return
        else:
            config = None
    else:
        config = load_repo_config(ctf_config)

    VIOLATION_STYLES = {
        SeverityLevel.FATAL: ("ctfa.lint.level.fatal", "✕"),
        SeverityLevel.ERROR: ("ctfa.lint.level.error", "✕"),
        SeverityLevel.WARNING: ("ctfa.lint.level.warning", "⚠"),
        SeverityLevel.INFO: ("ctfa.lint.level.info", "🛈"),
    }

    result = lint_challenge(chall_path, ctf_config=config, level=level, ignore=ignore)

    if result.failed or result.errors:
        if result.errors:
            challenge_label = f"{chall_path.name} ({len(result.failed)} violations, {len(result.errors)} errors)"

            highest_severity = SeverityLevel.FATAL
        else:
            challenge_label = f"{chall_path.name} ({len(result.failed)} violations)"

            highest_severity = level

        challenge_tree = Tree(challenge_label)

        for error in result.errors:
            challenge_tree.add(
                f"✕ ERROR - {error.code} - {error.message}",
                style="ctfa.lint.error",
            )

        for failed in result.failed:
            if failed.level > highest_severity:
                highest_severity = failed.level

            style, icon = VIOLATION_STYLES[failed.level]

            challenge_tree.add(
                f"{icon} {failed.code} - {failed.message}",
                style=style,
            )

        challenge_tree.style = VIOLATION_STYLES[highest_severity][0]

    else:
        challenge_tree = Tree(f"{chall_path.name} (all passed)")

    if show_skipped and result.skipped:
        for skipped in result.skipped:
            challenge_tree.add(
                f"⏩ SKIPPED - {skipped.code} - {skipped.message}",
                style="ctfa.lint.skipped",
            )

    if show_ignored and result.ignored:
        for ignored in result.ignored:
            challenge_tree.add(
                f"🚫 IGNORED - {ignored.code} - {ignored.message}",
                style="ctfa.lint.ignored",
            )

    if show_passed and result.passed:
        for passed in result.passed:
            challenge_tree.add(
                f"✓ PASSED - {passed.code}",
                style="ctfa.lint.passed",
            )

    if len(challenge_tree.children) == 0:
        challenge_tree.add("✓ All checks passed", style="ctfa.lint.passed")

    challenge_panel = Panel(
        challenge_tree,
        title=f"{chall_path.name} Lint Results",
        style="ctfa.info",
        border_style="green",
    )

    console.print(challenge_panel)
    console.print()  # Add spacing


@app.command(group="Updating")
def update(
    chall_path: Annotated[ResolvedExistingDirectory | None, Parameter(name=["--path", "-p"])] = None,
    *,
    remake_config: Annotated[bool, Parameter(name=["--remake-config", "-c"], negative="")] = False,
):
    """Update the challenge's README, and optionally remake the config.

    Args:
        chall_path (ResolvedExistingDirectory, optional): The path to the challenge directory. If not specified, the current directory is used.
        remake_config (bool, optional): Whether to remake the config.
    """
    if chall_path is None:
        chall_path = Path.cwd()

    if not is_challenge_folder(chall_path):
        console.print(":x: Specified path is not a challenge folder.", style="ctfa.error")
        return

    chall_config = load_chall_config(chall_path)

    save_chall_readme(chall_path, chall_config)

    if remake_config:
        save_chall_config(chall_path, chall_config)

    console.print(
        ":sparkles: Challenge updated! :sparkles:",
        style="ctfa.success",
    )
