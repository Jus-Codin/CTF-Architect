from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.tree import Tree

from ctf_architect._console import console
from ctf_architect.core.config import load_config
from ctf_architect.core.lint import Linter, LintResult, SeverityLevel

lint_app = typer.Typer()


@lint_app.callback()
def callback():
    """
    Commands to lint the challenges in the CTF repo.
    """


@lint_app.command("run")
def lint_run(
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
    show_passed: Annotated[
        bool,
        typer.Option(
            "--show-passed",
            "-s",
            help="Show challenges that passed linting.",
        ),
    ] = False,
):
    """
    Lint the challenges in the CTF repo.
    """

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

    try:
        config = load_config()
    except FileNotFoundError:
        console.print(
            "Could not find CTF config file. Are you in the right directory?",
            style="bright_red",
        )
        return

    linter = Linter(ctf_config=config, level=level, ignore=ignore)

    # {
    #     "category": {
    #         "passed": {
    #             "challenge": LintResult,
    #         },
    #         "failed": {
    #             "challenge": LintResult,
    #         },
    #     }
    # }
    results: dict[str, dict[Literal["passed", "failed"], dict[str, LintResult]]] = {}

    challenges_path = Path("challenges")

    for category in config.categories:
        results[category] = {"passed": {}, "failed": {}}

        for directory in (challenges_path / category).iterdir():
            if directory.is_dir():
                result = linter.lint(directory)
                if result["violations"]:
                    results[category]["failed"][directory.name] = result
                else:
                    results[category]["passed"][directory.name] = result

    LEVEL_MAP = {
        SeverityLevel.FATAL: ("bright_magenta", "✕"),
        SeverityLevel.ERROR: ("bright_red", "✕"),
        SeverityLevel.WARNING: ("bright_yellow", "⚠"),
        SeverityLevel.INFO: ("bright_cyan", "🛈"),
    }

    failed_results = sum(len(cat["failed"]) for cat in results.values())

    if failed_results == 0:
        root_label = "challenges/ (all passed)"
    else:
        root_label = f"challenges/ ({failed_results} failed)"

    tree = Tree(root_label)

    for category, category_results in results.items():
        failed = len(category_results["failed"])

        if failed == 0:
            category_label = f"{category}/ (all passed)"
        else:
            category_label = f"{category}/ ({failed} failed)"

        category_node = tree.add(category_label)

        if not show_passed and failed == 0:
            category_node.add("✓ All challenges passed", style="bright_green")
            continue

        for challenge_name, result in category_results["failed"].items():
            challenge_node = category_node.add(
                f"{challenge_name} ({len(result['violations'])} violations)"
            )

            highest_severity = SeverityLevel.INFO

            for violation in result["violations"]:
                if violation["level"] > highest_severity:
                    highest_severity = violation["level"]

                style, icon = LEVEL_MAP[violation["level"]]
                challenge_node.add(
                    f"{icon} {violation['code']} - {violation['message']}",
                    style=style,
                )

            challenge_node.style = LEVEL_MAP[highest_severity][0]

        if show_passed:
            for challenge_name, result in category_results["passed"].items():
                challenge_node = category_node.add(
                    f"{challenge_name} (passed)", style="bright_green"
                )
                challenge_node.add("✓ All rules passed", style="bright_green")

    console.rule("Lint Results")
    console.print(tree)
