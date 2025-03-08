from __future__ import annotations

import re
from pathlib import Path

# from ctf_architect.cli.ui._filedialog import askdirectory, askopenfilename, askopenfilenames
from ctf_architect.cli.ui.components import create_repo_config_panels
from ctf_architect.cli.ui.console import console
from ctf_architect.cli.ui.prompts import confirm, input_str, select
from ctf_architect.cli.ui.prompts.session import InvalidResponse
from ctf_architect.core.repo import load_repo_config


def ask_repo_config():
    from ctf_architect.cli.ui._filedialog import askopenfilename

    while True:
        console.print("Please select the Repo Configuration file.", style="ctfa.info")

        config_file_path = askopenfilename(
            title="Select Repo Configuration file",
            filetypes=[("Repo Configuration file", "*.toml")],
        )

        if not config_file_path:
            return None

        config = load_repo_config(config_file_path)

        for panel in create_repo_config_panels(
            name=config.name,
            flag_format=config.flag_format,
            starting_port=config.starting_port,
            categories=config.categories,
            difficulties=config.difficulties,
            extras=config.extras,
        ):
            console.print(panel)

        if confirm("Is this the correct Repo Configuration?").execute():
            return config

        # Spacing
        console.print()


def valid_chall_name(name: str) -> bool:
    return not not re.sub(r"^[^a-zA-Z]+|[^a-zA-Z0-9 _-]", "", name).strip()


def valid_service_folder(path: Path) -> bool:
    if not path.is_dir() or not path.exists():
        return False

    # Check if there is a Dockerfile or docker-compose.yml in the folder, case-insensitive
    return any(
        file.name.lower()
        in (
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        )
        for file in path.iterdir()
    )


def _validate_file_path(response: str):
    try:
        path = Path(response)
    except Exception:
        raise InvalidResponse("[ctfa.prompt.error]Invalid file path.")

    if not path.exists():
        raise InvalidResponse("[ctfa.prompt.error]File does not exist.")

    if not path.is_file():
        raise InvalidResponse("[ctfa.prompt.error]Path is not a file.")


def _validate_service_folder_path(response: str):
    try:
        path = Path(response)
    except Exception:
        raise InvalidResponse("[ctfa.prompt.error]Invalid folder path.")

    if not path.exists():
        raise InvalidResponse("[ctfa.prompt.error]Folder does not exist.")

    if not path.is_dir():
        raise InvalidResponse("[ctfa.prompt.error]Path is not a folder.")

    if not valid_service_folder(path):
        raise InvalidResponse("[ctfa.prompt.error]Folder does not contain a Dockerfile.")


def ask_dist_files() -> list[Path | str]:
    from ctf_architect.cli.ui._filedialog import askopenfilenames

    files = []

    while True:
        file_type = select(
            choices=["Local file", "URL", "Done"],
            prompt="Select the type of files to add",
        ).execute()

        if file_type == "Local file":
            input_method = select(
                choices=["Manually enter path", "Browse for file"],
                prompt="How would you like to select the file?",
            ).execute()

            if input_method == "Manually enter path":
                try:
                    file_path = input_str(
                        ":file_folder: Enter the path to the file",
                        allow_empty=False,
                        validator=_validate_file_path,
                    ).execute()
                except KeyboardInterrupt:
                    continue

                files.append(Path(file_path))

                console.print(f"Added file: {file_path}", style="ctfa.success")
            else:
                file_paths = askopenfilenames(title="Select the dist files for the challenge")
                if file_paths == "":
                    # User cancelled or dialog is unsupported
                    continue

                for file_path in file_paths:
                    files.append(Path(file_path))

                    console.print(f"Added file: {file_path}", style="ctfa.success")
        elif file_type == "URL":
            # TODO: Add URL validation
            url = input_str(":file_folder: Enter the URL of the file", allow_empty=False).execute()
            files.append(url)

            console.print(f"Added URL: {url}", style="ctfa.success")
        else:
            break

        # Spacing
        console.print()

    if not files:
        console.print(":warning: No files were added.", style="ctfa.warning")

    return files


def ask_source_files() -> list[Path]:
    from ctf_architect.cli.ui._filedialog import askopenfilename

    files = []

    while True:
        input_method = select(
            choices=["Manually enter path", "Browse for file", "Done"],
            prompt="How would you like to select the file?",
        ).execute()

        if input_method == "Manually enter path":
            try:
                file_path = input_str(
                    ":file_folder: Enter the path to the file",
                    allow_empty=False,
                    validator=_validate_file_path,
                ).execute()
            except KeyboardInterrupt:
                continue

            files.append(Path(file_path))

            console.print(f"Added file: {file_path}", style="ctfa.success")
        elif input_method == "Browse for file":
            file_path = askopenfilename(title="Select the source file for the challenge")
            if file_path == "":
                # User cancelled or dialog is unsupported
                continue

            files.append(Path(file_path))

            console.print(f"Added file: {file_path}", style="ctfa.success")
        else:
            break

        # Spacing
        console.print()

    if not files:
        console.print(":warning: No files were added.", style="ctfa.warning")

    return files


def ask_solution_files() -> list[Path]:
    from ctf_architect.cli.ui._filedialog import askopenfilename

    files = []

    while True:
        input_method = select(
            choices=["Manually enter path", "Browse for file", "Done"],
            prompt="How would you like to select the file?",
        ).execute()

        if input_method == "Manually enter path":
            try:
                file_path = input_str(
                    ":file_folder: Enter the path to the file",
                    allow_empty=False,
                    validator=_validate_file_path,
                ).execute()
            except KeyboardInterrupt:
                continue

            files.append(Path(file_path))

            console.print(f"Added file: {file_path}", style="ctfa.success")
        elif input_method == "Browse for file":
            file_path = askopenfilename(title="Select the solution file for the challenge")
            if file_path == "":
                # User cancelled or dialog is unsupported
                continue

            files.append(Path(file_path))

            console.print(f"Added file: {file_path}", style="ctfa.success")
        else:
            break

        # Spacing
        console.print()

    if not files:
        console.print(":warning: No files were added.", style="ctfa.warning")

    return files


def ask_service_folder() -> Path | None:
    from ctf_architect.cli.ui._filedialog import askdirectory

    folder = None

    while True:
        input_method = select(
            choices=["Manually enter path", "Browse for folder", "Cancel"],
            prompt="How would you like to select the folder?",
        ).execute()

        if input_method == "Manually enter path":
            try:
                folder_path = input_str(
                    ":file_folder: Enter the path to the folder",
                    allow_empty=False,
                    validator=_validate_service_folder_path,
                ).execute()
            except KeyboardInterrupt:
                continue

            folder = Path(folder_path)

            console.print(f"Selected folder: {folder_path}", style="ctfa.success")
            break

        if input_method == "Browse for folder":
            while True:
                folder_path = askdirectory(title="Select the service folder")

                if folder_path == "":
                    # User cancelled or dialog is unsupported
                    folder = None
                    break

                folder = Path(folder_path)

                if not valid_service_folder(folder):
                    console.print(
                        ":x: Invalid service folder, must contain a Dockerfile or Docker Compose file.",
                        style="ctfa.error",
                    )
                    continue

                break

            if folder is None:
                # User cancelled or dialog is unsupported
                continue

            console.print(f"Selected folder: {folder_path}", style="ctfa.success")
            break

        break

    return folder
