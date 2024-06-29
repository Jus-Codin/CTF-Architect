from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path
from zipfile import ZipFile

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ctf_architect.core.challenge import (
    add_challenge,
    find_challenge,
    is_challenge_folder,
    is_challenge_repo,
    verify_challenge_config,
    walk_challenges,
)
from ctf_architect.core.config import load_config
from ctf_architect.core.constants import APP_CMD_NAME, CTF_CONFIG_FILE
from ctf_architect.core.stats import update_category_readme, update_root_readme

console = Console()


challenge_app = typer.Typer()


@challenge_app.callback()
def callback():
    """
    Commands to manage challenges in the CTF repo.
    """


@challenge_app.command("import")
def challenge_import(
    path: str = typer.Option(
        default=".", help="Specify the path to ther challenge zip files."
    ),
    delete_on_error: bool = typer.Option(
        False,
        "--delete-on-error",
        "-d",
        help="Delete the challenge folder if an error occurs.",
    ),
    replace: bool = typer.Option(
        False, "--replace", "-r", help="Replace the challenge if it already exists."
    ),
    update_stats: bool = typer.Option(
        True,
        "--update-stats",
        "-u",
        help="Update the stats after importing the challenge.",
    ),
):
    """
    Imports all challenges from the specified directory to the CTF repo.
    """

    try:
        config = load_config()
    except FileNotFoundError:
        console.print(
            "Could not find CTF config file. Are you in the right directory?",
            style="bright_red",
        )
        return

    zip_path = Path(path)
    extracted_path = Path("extracted")

    if not zip_path.exists():
        console.print(
            f"Could not find the specified path: {zip_path}", style="bright_red"
        )
        return

    if not zip_path.is_dir():
        console.print("The specified path must be a directory", style="bright_red")
        return

    success = 0
    unzip_failed = 0
    import_failed = 0

    for zip_file in zip_path.glob("*.zip"):
        new_path = extracted_path / zip_file.name.rsplit(".", 1)[0]

        try:
            # Extract the files to the "extracted" folder
            with ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(new_path)
        except Exception as e:
            console.print(f"Error extracting {zip_file}:\n{e}", style="bright_red")
            unzip_failed += 1
            continue

        # Zipfile could contain multiple folders, recurse through every folder
        # as deep as possible until there is a challenge config file
        challenge_folders: list[Path] = []

        queue: deque[Path] = deque()
        queue.append(new_path)
        # BFS through the extracted folder
        while queue:
            current = queue.popleft()
            if is_challenge_folder(current):
                challenge_folders.append(current)
            else:
                for item in current.iterdir():
                    if item.is_dir():
                        queue.append(item)

        if not challenge_folders:
            console.print(
                f"No challenge folders found in {zip_file}, skipping...", style="yellow"
            )
            if delete_on_error:
                shutil.rmtree(new_path, ignore_errors=True)
            continue

        folder_is_success = True
        for extracted in challenge_folders:
            try:
                add_challenge(extracted, replace=replace)
            except FileExistsError:
                if Confirm.ask(
                    f"[cyan]Challenge {extracted.name} already exists. Do you want to replace it?[/]"
                ):
                    try:
                        add_challenge(extracted, replace=True)
                    except Exception as e:
                        console.print(
                            f"Error importing {extracted.name}:\n{e}",
                            style="bright_red",
                        )
                        # Delete the challenge folder if it exists
                        if extracted.exists() and delete_on_error:
                            shutil.rmtree(extracted)
                        else:
                            folder_is_success = False
                        import_failed += 1
                        continue
                    else:
                        console.print(
                            f'Challenge "{extracted.name}" imported successfully.',
                            style="green",
                        )
                        # Delete the extracted folder
                        shutil.rmtree(extracted, ignore_errors=True)
                        success += 1
                    console.print(f'Skipping "{extracted.name}"', style="yellow")
            except Exception as e:
                console.print(
                    f"Error importing {extracted.name}:\n{e}", style="bright_red"
                )
                # Delete the challenge folder if it exists
                if extracted.exists() and delete_on_error:
                    shutil.rmtree(extracted)
                else:
                    folder_is_success = False
                import_failed += 1
                continue
            else:
                console.print(
                    f'Challenge "{extracted.name}" imported successfully.',
                    style="green",
                )
                # Delete the extracted folder
                shutil.rmtree(extracted, ignore_errors=True)
                success += 1

        # If all challenges in the folder were imported successfully, delete the folder
        if folder_is_success:
            shutil.rmtree(new_path, ignore_errors=True)

    if update_stats and success > 0:
        for category in config.categories:
            update_category_readme(category)

        update_root_readme()

        console.print("Repo READMEs updated successfully.", style="green")


@challenge_app.command("export")
def challenge_export(
    name: str = typer.Argument(..., help="Name of the challenge to export."),
    path: str = typer.Option(
        ".", "--path", "-p", help="Path to export the challenge to."
    ),
    filename: str | None = typer.Option(
        None, "--filename", "-f", help="Filename of the exported challenge."
    ),
):
    """
    Exports the challenge as a zip file
    """

    if not is_challenge_repo():
        console.print("Not a valid challenge repo. Exiting...", style="bright_red")
        return

    challenge = find_challenge(name)

    if challenge is None:
        console.print(f"Could not find challenge: {name}", style="bright_red")
        return

    challenge_path = challenge[1]

    if filename is None:
        filename = challenge_path.name

    path = Path(path) / filename

    zip_path = shutil.make_archive(path, "zip", challenge_path)

    console.print(f"Challenge exported to {zip_path}", style="green")


@challenge_app.command("info")
def challenge_info(name: str = typer.Argument(..., help="Name of the challenge.")):
    """
    Display information about a challenge
    """

    if not is_challenge_repo():
        console.print("Not a valid challenge repo. Exiting...", style="bright_red")
        return

    challenge = find_challenge(name)

    if challenge is None:
        console.print(f"Could not find challenge: {name}", style="bright_red")
        return

    config, path = challenge

    info = (
        f"[bold]Name:[/] {config.name}\n"
        f"[bold]Description:[/] {config.description.strip()}\n\n"
        f"[bold]Difficulty:[/] {config.difficulty.capitalize()}\n"
        f"[bold]Category:[/] {config.category.capitalize()}\n"
        f"[bold]Author:[/] {config.author}\n"
    )

    for extra in config.extras:
        info += f"[bold]{extra.capitalize()}[/]: {config.extras[extra]}\n"

    if config.services is not None:
        info += "\n[bold]Services[/]:\n"
        for service in config.services:
            info += (
                f"\n - [bold]Name:[/] {service.name}\n"
                # f" - [bold]Path:[/] {service.path}\n"
                f" - [bold]Path:[/] {(path / service.path).resolve()}\n"
                f" - [bold]Port:[/] {service.port}\n"
                f" - [bold]Type:[/] {service.type.capitalize()}\n"
            )

    console.print(
        Panel.fit(
            info,
            title=f'Challenge Info for "{config.name}" ({path.resolve()})',
            border_style="bright_cyan",
        )
    )


@challenge_app.command("verify")
def challenge_verify():
    """
    Verify the challenges in the CTF repo
    """

    if not is_challenge_repo():
        console.print("Not a valid challenge repo. Exiting...", style="bright_red")
        return

    config = load_config()

    total = 0
    failed = 0

    for chall in walk_challenges():
        total += 1
        try:
            verify_challenge_config(chall, config)
        except Exception as e:
            console.print(f"Error verifying {chall.name}:\n{e}", style="bright_red")
            failed += 1

    if failed == 0:
        console.print("All challenges verified successfully.", style="green")
    else:
        console.print(
            f"{failed}/{total} challenges failed verification.", style="bright_red"
        )
