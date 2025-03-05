from __future__ import annotations

from collections import deque
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from zipfile import ZipFile

from cyclopts import App, Parameter
from cyclopts.types import ResolvedExistingDirectory
from rich.panel import Panel
from rich.tree import Tree

from ctf_architect.cli.commands.repo.compose import app as compose_app
from ctf_architect.cli.commands.repo.config import app as config_app
from ctf_architect.cli.commands.repo.mapping import app as mapping_app
from ctf_architect.cli.commands.repo.stats import app as stats_app
from ctf_architect.cli.ui.components import create_repo_config_panels
from ctf_architect.cli.ui.console import console
from ctf_architect.cli.ui.prompts import (
    InvalidResponse,
    confirm,
    input_int,
    input_str,
    select,
)
from ctf_architect.cli.validators import no_empty_string, valid_port
from ctf_architect.constants import CTF_CONFIG_FILE
from ctf_architect.core.challenge import is_challenge_folder
from ctf_architect.core.exceptions import ChallengeExistsError
from ctf_architect.core.initialize import init_repo_from_config, init_repo_no_config
from ctf_architect.core.lint import lint_challenge, lint_challenge_repo
from ctf_architect.core.repo import (
    add_challenge,
    find_challenge,
    find_challenge_folder,
    is_challenge_repo,
    load_repo_config,
)
from ctf_architect.core.stats import update_category_readme, update_root_readme
from ctf_architect.models.lint import LintResult, SeverityLevel

app = App(
    name="repo",
    group="Subcommands",
    help="Commands for managing the challenge repository.",
)

app.command(compose_app)
app.command(config_app)
app.command(mapping_app)
app.command(stats_app)


@app.command(group="Initialization")
def init(
    *,
    config_only: Annotated[bool, Parameter(name=["--config-only", "-c"], negative="")] = False,
    name: Annotated[str | None, Parameter(name=["--name", "-n"], group="CTF Config")] = None,
    categories: Annotated[
        list[str] | None,
        Parameter(
            name=["--category", "-c"],
            group="CTF Config",
            negative="",
            consume_multiple=True,
        ),
    ] = None,
    difficulties: Annotated[
        list[str] | None,
        Parameter(
            name=["--difficulty", "-d"],
            group="CTF Config",
            negative="",
            consume_multiple=True,
        ),
    ] = None,
    flag_format: Annotated[str | None, Parameter(name=["--flag-format", "-f"], group="CTF Config")] = None,
    starting_port: Annotated[int | None, Parameter(name=["--starting-port", "-p"], group="CTF Config")] = None,
):
    """Initialize a new challenge repository.

    Args:
        name (str | None, optional): The name of the CTF. Defaults to None.
        categories (list[str], optional): The list of categories for the CTF. Defaults to None.
        difficulties (list[str], optional): The list of difficulties for the CTF. Defaults to None.
        flag_format (str, optional): The flag format for the CTF. Defaults to None.
        starting_port (int, optional): The starting port for services in the CTF. Defaults to None.
        config_only (bool, optional): Whether to only save the config file. Defaults to False.
    """
    if Path(CTF_CONFIG_FILE).exists():
        if config_only:
            console.print("A config file already exists. Exiting...", style="ctfa.error")
            return

        choice = select(
            prompt="A config file already exists. What would you like to do?",
            choices=[
                "Use existing config",
                "Overwrite existing config",
                "Abort",
            ],
            prompt_suffix="",
        ).execute()

        if choice == "Abort":
            console.print("Aborting...", style="ctfa.error")
            return

        elif choice == "Use existing config":
            if any([name, categories, difficulties, flag_format, starting_port]):
                console.print(":warning: Ignoring provided arguments...", style="ctfa.warning")

            init_repo_from_config()
            console.print(
                ":sparkles: Challenge repository initialized! :sparkles:",
                style="ctfa.success",
            )
            return

        elif choice == "Overwrite existing config":
            console.print(":warning: Overwriting existing config...", style="ctfa.warning")

    if not name:
        name = input_str(prompt="Enter the name of the CTF", validator=no_empty_string).execute()

    console.print(f"CTF Name: {name}", style="ctfa.info")

    if flag_format is None and confirm("Would you like to specify a flag format?").execute():
        flag_format = input_str("Enter the flag format").execute()

    console.print()
    console.print(f"Flag Format: {flag_format if flag_format else 'None'}", style="ctfa.info")

    if starting_port is None and confirm("Would you like to specify a starting port?").execute():
        starting_port = input_int("Enter the starting port", validator=valid_port).execute()

    console.print()
    console.print(
        f"Starting Port: {starting_port if starting_port else 'None'}",
        style="ctfa.info",
    )

    console.print()
    console.rule("[ctfa.title]Challenge Categories[/ctfa.title]")

    if not categories:
        _categories = []

        def _at_least_one_category(response: str) -> None:
            if response == "" and not _categories:
                raise InvalidResponse("[ctfa.prompt.error]At least one category is required")

        console.print(
            "Enter the categories for the CTF (one per line, empty line to stop).",
            style="ctfa.info",
        )

        while True:
            category = input_str("Category Name (empty to stop)", validator=_at_least_one_category).execute()

            if category == "":
                break

            _categories.append(category.lower())
            console.print(f'Category "{category}" added.', style="ctfa.success")

            # Add spacing
            console.print()

        categories = _categories

    console.print("Categories:", style="ctfa.info")
    for category in categories:
        console.print(f"  - {category.capitalize()}", style="ctfa.info")

    console.print()
    console.rule("[ctfa.title]Challenge Difficulties[/ctfa.title]")

    if not difficulties:
        _difficulties = []

        def _at_least_one_difficulty(response: str) -> None:
            if response == "" and not _difficulties:
                raise InvalidResponse("[ctfa.prompt.error]At least one difficulty is required")

        console.print(
            "Enter the difficulties for the CTF (empty name to stop).",
            style="ctfa.info",
        )

        while True:
            difficulty = input_str("Difficulty Name (empty to stop)", validator=_at_least_one_difficulty).execute()

            if difficulty == "":
                break

            _difficulties.append(difficulty)
            console.print(f'Difficulty "{difficulty}" added.', style="ctfa.success")

            # Add spacing
            console.print()

        difficulties = _difficulties

    console.print("Difficulties:", style="ctfa.info")
    for difficulty in difficulties:
        console.print(f"  - {difficulty.capitalize()}", style="ctfa.info")

    console.print()
    console.rule("[ctfa.title]Extra Fields[/ctfa.title]")

    if confirm("Would you like to specify extra fields for challenges?").execute():
        # Add spacing
        console.print()

        extras = []

        while True:
            extra_name = input_str("Extra Field Name (empty to cancel)").execute()

            if extra_name == "":
                break

            extra_description = input_str("Extra Field Description").execute()

            extra_prompt = input_str("Extra Field Prompt (shown to challenge creators)").execute()

            extra_required = confirm("Is this extra field required?").execute()

            extra_type = select(
                prompt="Extra Field Type",
                choices=["string", "integer", "float", "boolean"],
            ).execute()

            extras.append(
                {
                    "name": extra_name,
                    "description": extra_description,
                    "prompt": extra_prompt,
                    "required": extra_required,
                    "type": extra_type,
                }
            )

            console.print(f'Extra Field "{extra_name}" added.', style="ctfa.success")

            if not confirm("Add another extra field?").execute():
                break

            # Add spacing
            console.print()

        if not extras:
            console.print("No extra fields specified.", style="ctfa.warning")
            extras = None
    else:
        extras = None

    console.print("Extra Fields:", style="ctfa.info")
    if extras:
        for extra in extras:
            console.print(f"  - {extra['name']} ({extra['type']})", style="ctfa.info")
    else:
        console.print("  - None", style="ctfa.info")

    # ctf_config_panel = Panel(
    #     (
    #         f" CTF Name: {name}\n"
    #         f" Flag Format: {flag_format if flag_format else 'None'}\n"
    #         f" Starting Port: {starting_port if starting_port else 'None'}\n"
    #     ),
    #     title="CTF Config",
    #     title_align="left",
    #     style="ctfa.info",
    #     border_style="green",
    # )

    # categories_panel = Panel(
    #     "\n".join([f"  - {category.capitalize()}" for category in categories]),
    #     title="Categories",
    #     title_align="left",
    #     style="ctfa.info",
    #     border_style="green",
    # )

    # difficulties_panel = Panel(
    #     "\n".join([f"  - {difficulty.capitalize()}" for difficulty in difficulties]),
    #     title="Difficulties",
    #     title_align="left",
    #     style="ctfa.info",
    #     border_style="green",
    # )

    # extras_panel = Panel(
    #     "\n".join([f"  - {extra['name']} ({extra['type']})" for extra in extras])
    #     if extras
    #     else "  - None",
    #     title="Extras",
    #     title_align="left",
    #     style="ctfa.info",
    #     border_style="green",
    # )

    # console.print(ctf_config_panel)
    # console.print(categories_panel)
    # console.print(difficulties_panel)
    # console.print(extras_panel)

    for panel in create_repo_config_panels(
        name=name,
        flag_format=flag_format,
        starting_port=starting_port,
        categories=categories,
        difficulties=difficulties,
        extras=extras,  # type: ignore
    ):
        console.print(panel)

    if confirm("Are you sure you want to create this Challenge Repository?").execute():
        init_repo_no_config(
            name=name,
            categories=categories,
            difficulties=difficulties,
            flag_format=flag_format,
            starting_port=starting_port,
            extras=extras,
            config_only=config_only,
        )

        console.print(
            ":sparkles: Challenge repository initialized! :sparkles:",
            style="ctfa.success",
        )
    else:
        console.print("Aborting...", style="ctfa.error")
        return


@app.command(name="import", group="Challenges")
def challenge_import(
    *,
    directory: Annotated[ResolvedExistingDirectory, Parameter(name=["--dir", "-d"])] = Path.cwd(),
    replace: Annotated[bool, Parameter(name=["--replace", "-r"], negative="")] = False,
    no_update_stats: Annotated[bool, Parameter(name=["--no-update-stats", "-n"], negative="")] = False,
):
    """Import challenges from a directory.

    Args:
        directory (ResolvedExistingDirectory): The directory to import challenges from.
        replace (bool, optional): Whether to overwrite existing challenges. Defaults to False.
        no_update_stats (bool, optional): Whether to skip updating repo stats. Defaults to False.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    success = 0
    unzip_failed: list[Path] = []
    import_failed: list[str] = []

    with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
        temp_path = Path(temp_dir)

        for zip_file in directory.glob("*.zip"):
            target_path = temp_path / zip_file.stem

            try:
                with ZipFile(zip_file, "r") as zip_ref:
                    zip_ref.extractall(target_path)
            except Exception:
                console.print(f"Failed to extract {zip_file}", style="ctfa.error")
                console.print_exception()
                unzip_failed.append(zip_file)
                continue

            challenge_folders: list[Path] = []

            # Check if the extracted folder is a challenge folder
            if is_challenge_folder(target_path):
                challenge_folders.append(target_path)
            else:
                # Recursively search for challenge folders
                queue = deque([target_path])

                # BFS through the extracted folder
                while queue:
                    current = queue.popleft()

                    if is_challenge_folder(current):
                        challenge_folders.append(current)
                    else:
                        for file in current.iterdir():
                            if file.is_dir():
                                queue.append(file)

            if not challenge_folders:
                console.print(
                    f":warning: No challenge folders found in {zip_file}",
                    style="ctfa.warning",
                )
                continue

            for challenge_folder in challenge_folders:
                asked_allow_replace = replace

                while True:
                    try:
                        add_challenge(challenge_folder, asked_allow_replace)

                        console.print(
                            f"Successfully imported {challenge_folder.name}",
                            style="ctfa.success",
                        )

                        success += 1
                        break
                    except ChallengeExistsError:
                        if not confirm(f"Challenge already exists. Replace {challenge_folder.name}?").execute():
                            break
                        asked_allow_replace = True
                    except Exception as e:
                        console.print(
                            f"Failed to import {challenge_folder.name}: {e}",
                            style="ctfa.error",
                        )
                        import_failed.append(challenge_folder.name)
                        break

    if not no_update_stats and success > 0:
        console.print("Updating stats...", style="ctfa.info")

        for category in config.categories:
            update_category_readme(category)

        update_root_readme()

        console.print(":sparkles: Repository stats updated.", style="ctfa.info")

    if unzip_failed:
        console.print(f":x: Failed to extract {len(unzip_failed)} zip files.", style="ctfa.error")

    if import_failed:
        console.print(f":x: Failed to import {len(import_failed)} challenges.", style="ctfa.error")

    console.print(
        f":sparkles: Successfully imported {success} challenges. :sparkles:",
        style="ctfa.success",
    )


@app.command(name="export", group="Challenges")
def challenge_export(
    name: Annotated[str, Parameter(name=["--name", "-n"])],
    *,
    path: Annotated[ResolvedExistingDirectory, Parameter(name=["--path", "-p"])] = Path.cwd(),
    file_name: Annotated[str | None, Parameter(name=["--filename", "-f"])] = None,
):
    """Export challenges to a zip file.

    Args:
        name (str): The name of the challenge to export.
        path (ResolvedExistingDirectory, optional): The path to the zip file to export to. Defaults to the current directory.
        file_name (str, optional): The name of the zip file to export to. Defaults to None.
    """
    if not is_challenge_repo():
        console.print(
            "This is not a challenge repository. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    challenge = find_challenge(name)

    if challenge is None:
        console.print(f"Could not find challenge: {name}", style="ctfa.error")
        return

    if file_name is None:
        file_name = f"{challenge.folder_name}.zip"

    zip_path = path / file_name

    with ZipFile(zip_path, "w") as zip_ref:
        for file in challenge.repo_path.rglob("*"):
            zip_ref.write(file, file.relative_to(challenge.repo_path))

    console.print(f"Successfully exported challenge to {zip_path}", style="ctfa.success")


@app.command(group="Linting")
def lint(
    challenges: Annotated[
        list[str] | None,
        Parameter(name=["--challenge", "-c"], negative="", consume_multiple=True),
    ] = None,
    *,
    level: Annotated[SeverityLevel, Parameter(name=["--level", "-l"])] = SeverityLevel.WARNING,
    ignore: Annotated[
        list[str] | None,
        Parameter(name=["--ignore", "-i"], negative="", consume_multiple=True),
    ] = None,
    show_passed: Annotated[bool, Parameter(name=["--show-passed", "-P"], negative="")] = False,
    show_ignored: Annotated[bool, Parameter(name=["--show-ignored", "-I"], negative="")] = False,
    show_skipped: Annotated[bool, Parameter(name=["--show-skipped", "-S"], negative="")] = False,
):
    """Lint the challenges in the CTF repo.

    Args:
        challenges (list[str], optional): List of challenge names to lint. Defaults to None.
        level (SeverityLevel, optional): Minimum severity level to lint for. Defaults to SeverityLevel.WARNING.
        ignore (list[str], optional): List of rule codes to ignore. Defaults to None.
        show_passed (bool, optional): Show challenges that passed linting. Defaults to False.
        show_ignored (bool, optional): Show rules that were ignored. If no challenge is specified, this flag does nothing. Defaults to False.
        show_skipped (bool, optional): Show rules that were skipped. If no challenge is specified, this flag does nothing. Defaults to False.
    """
    try:
        config = load_repo_config()
    except FileNotFoundError:
        console.print(
            "Could not find Repository config file. Are you in the right directory?",
            style="ctfa.error",
        )
        return

    VIOLATION_STYLES = {
        SeverityLevel.FATAL: ("ctfa.lint.level.fatal", "✕"),
        SeverityLevel.ERROR: ("ctfa.lint.level.error", "✕"),
        SeverityLevel.WARNING: ("ctfa.lint.level.warning", "⚠"),
        SeverityLevel.INFO: ("ctfa.lint.level.info", "🛈"),
    }

    # Lint all challenges
    if challenges is None:
        results = lint_challenge_repo(level=level, ignore=ignore, by_category=True)

        failed_challenges = [
            result for category in results.values() for result in category.values() if result.failed or result.errors
        ]

        if len(failed_challenges) == 0:
            root_label = "challegnes/ (all passed)"
        else:
            root_label = f"challenges/ ({len(failed_challenges)} failed)"

        tree = Tree(root_label)

        for category, category_results in results.items():
            category_passed: dict[str, LintResult] = {}
            category_failed: dict[str, LintResult] = {}

            for challenge, result in category_results.items():
                if result.failed or result.errors:
                    category_failed[challenge] = result
                else:
                    category_passed[challenge] = result

            if category_failed:
                category_label = f"{category}/ ({len(category_failed)} failed)"
            else:
                category_label = f"{category}/ (all passed)"

            category_tree = tree.add(category_label)

            if category_failed:
                for challenge, result in category_failed.items():
                    if result.errors:
                        challenge_tree = category_tree.add(
                            f"{challenge} ({len(result.failed)} violations, {len(result.errors)} errors)"
                        )

                        highest_severity = SeverityLevel.FATAL

                        # Always show errors first
                        for error in result.errors:
                            challenge_tree.add(
                                f"✕ ERROR - {error.code} - {error.message}",
                                style="ctfa.lint.error",
                            )
                    else:
                        challenge_tree = category_tree.add(f"{challenge} ({len(result.failed)} violations)")

                        highest_severity = level

                    for failed in result.failed:
                        if failed.level > highest_severity:
                            highest_severity = failed.level

                        style, icon = VIOLATION_STYLES[failed.level]

                        challenge_tree.add(f"{icon} {failed.code} - {failed.message}", style=style)

                    challenge_tree.style = VIOLATION_STYLES[highest_severity][0]

            elif not show_passed:
                # If no failed challenges and not showing passed, skip to next category
                category_tree.add("✓ All challenges passed", style="ctfa.lint.passed")

            # Show challenges that passed all checks
            if show_passed:
                for challenge, result in category_passed.items():
                    challenge_tree = category_tree.add(f"{challenge} (passed)", style="ctfa.lint.passed")
                    challenge_tree.add("✓ All checks passed", style="ctfa.lint.passed")

        lint_panel = Panel(tree, title="Lint Results", style="ctfa.info", border_style="green")

        console.print(lint_panel)

    # Lint specified challenges
    else:
        # Check if all challenges exist
        _challenge_paths: list[Path] = []

        for challenge_name in challenges:
            challenge_folder = find_challenge_folder(challenge_name)

            if challenge_folder is None:
                console.print(f"Could not find challenge: {challenge_name}", style="ctfa.error")
                return

            _challenge_paths.append(challenge_folder)

        for challenge_path in _challenge_paths:
            result = lint_challenge(challenge_path, ctf_config=config, level=level, ignore=ignore)

            if result.failed or result.errors:
                if result.errors:
                    challenge_label = (
                        f"{challenge_path.name} ({len(result.failed)} violations, {len(result.errors)} errors)"
                    )

                    highest_severity = SeverityLevel.FATAL
                else:
                    challenge_label = f"{challenge_path.name} ({len(result.failed)} violations)"

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

                    challenge_tree.add(f"{icon} {failed.code} - {failed.message}", style=style)

                challenge_tree.style = VIOLATION_STYLES[highest_severity][0]

            else:
                challenge_tree = Tree(f"{challenge_path.name} (all passed)")

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
                    challenge_tree.add(f"✓ PASSED - {passed.code}", style="ctfa.lint.passed")

            if len(challenge_tree.children) == 0:
                challenge_tree.add("✓ All checks passed", style="ctfa.lint.passed")

            challenge_panel = Panel(
                challenge_tree,
                title=f"{challenge_path.name} Lint Results",
                style="ctfa.info",
                border_style="green",
            )

            console.print(challenge_panel)
            console.print()  # Spacing


if __name__ == "__main__":
    app()
