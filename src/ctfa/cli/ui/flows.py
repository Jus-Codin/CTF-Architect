from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ctfa.cli.ui.console import console

if TYPE_CHECKING:
    from ctfa.models.challenge import ChallengeConfig
    from ctfa.models.ctf_config import CTFConfig


def ask_file(prompt: str, gui: bool = True, file_types: list[tuple[str, str]] | None = None) -> Path | None:
    while True:
        if gui:

            def _ask_file():
                from tkinter.filedialog import askopenfilename

                console.print(prompt, style="ctfa.prompt")

                file_path = askopenfilename(
                    title=prompt,
                    filetypes=file_types or [("All Files", "*.*")],
                )
                return Path(file_path) if file_path else None
        else:

            def _validator(response: str) -> bool | str:
                try:
                    path = Path(response)
                except Exception:
                    return "Invalid file path."

                if not path.exists():
                    return "File does not exist."

                if not path.is_file():
                    return "Path is not a file."

                return True

            def _filter(response: str) -> bool:
                if not file_types:
                    return True
                if os.path.isdir(response):
                    return True
                for _, ext in file_types:
                    if response.lower().endswith(ext.lower().lstrip("*")):
                        return True
                return False

            def _ask_file():
                # Questionary has a nice path prompt with auto-completion
                # so we just use that instead of rolling our own
                from questionary import path

                response = path(
                    prompt,
                    validate=_validator,
                    file_filter=_filter,
                ).ask()
                return Path(response) if response else None

        return _ask_file()


def ask_ctf_config(gui: bool = True) -> CTFConfig | None:
    while True:
        config_path = ask_file(
            "Please select the CTF Config file:",
            gui=gui,
            file_types=[("CTF Config file", "*.yaml"), ("CTF Config file", "*.yml")],
        )

        if config_path is None:
            return None

        from ctfa.cli.ui.components import CTFConfigComponent
        from ctfa.cli.ui.prompts import confirm
        from ctfa.core.repository import ChallengeRepository

        ctf_config = ChallengeRepository.load_config_file(config_path)

        console.print(CTFConfigComponent(ctf_config))

        if confirm("Is this the correct CTF Config").ask():
            return ctf_config

        # Spacing
        console.print()


def ask_ctf_config_details(
    name: str | None = None,
    categories: list[str] | None = None,
    difficulties: list[str] | None = None,
    flag_format: str | None = None,
    starting_port: int | None = None,
    interactive: bool = True,
    gui: bool = True,
) -> CTFConfig | None:
    from ctfa.cli.ui.components import CTFConfigComponent
    from ctfa.cli.ui.prompts import confirm, input_int, input_str, select
    from ctfa.models.ctf_config import CTFConfig

    if not interactive:
        extra_labels = None
    else:
        if name is None:
            name = input_str("Enter the CTF name", allow_empty=False).ask()
            console.print()  # Spacing

        if flag_format is None and confirm("Would you like to specify a flag format").ask():
            flag_format = input_str("Enter the flag format (regex)", allow_empty=False).ask()

        console.print()  # Spacing

        if starting_port is None and confirm("Would you like to specify a starting port for services").ask():
            starting_port = input_int(
                "Enter the starting port for services",
                validator=lambda r: "Starting port must be between 1 and 65535." if not (1 <= r <= 65535) else True,
            ).ask()

        console.print()  # Spacing

        if categories is None:
            categories = []

            def _at_least_one_category(response: str) -> bool | str:
                if response == "" and not categories:
                    return "At least one category must be specified."
                return True

            console.print("Enter the challenge categories (leave empty to finish):", style="ctfa.prompt")

            while True:
                _category = input_str(
                    "Category Name (empty to finish)",
                    validator=_at_least_one_category,
                    allow_empty=True,
                ).ask()

                if _category == "":
                    console.print()  # Spacing
                    break

                categories.append(_category)
                console.print(f"Category '{_category}' added.", style="ctfa.success")

                console.print()  # Spacing

        console.print("Categories:", style="ctfa.info")
        for cat in categories:
            console.print(f"- {cat}", style="ctfa.info")

        console.print()  # Spacing

        if difficulties is None:
            difficulties = []

            def _at_least_one_difficulty(response: str) -> bool | str:
                if response == "" and not difficulties:
                    return "At least one difficulty must be specified."
                return True

            console.print("Enter the challenge difficulties (leave empty to finish):", style="ctfa.prompt")

            while True:
                _difficulty = input_str(
                    "Difficulty Name (empty to finish)",
                    validator=_at_least_one_difficulty,
                    allow_empty=True,
                ).ask()

                if _difficulty == "":
                    console.print()  # Spacing
                    break

                difficulties.append(_difficulty)
                console.print(f"Difficulty '{_difficulty}' added.", style="ctfa.success")

                console.print()  # Spacing

        console.print("Difficulties:", style="ctfa.info")
        for diff in difficulties:
            console.print(f"- {diff}", style="ctfa.info")

        console.print()  # Spacing

        if confirm("Would you like to specify extra labels for challenges").ask():
            extra_labels = []

            while True:
                extra_name = input_str(
                    "Enter the extra label name (leave empty to cancel)",
                ).ask()

                if extra_name == "":
                    console.print()  # Spacing
                    break

                extra_type = select(
                    f"Select the type for the extra label '{extra_name}'",
                    choices=[
                        "string",
                        "integer",
                        "float",
                        "boolean",
                    ],
                ).ask()

                extra_description = input_str(
                    f"Enter the description for the extra label '{extra_name}'",
                ).ask()

                extra_prompt = input_str(
                    f"Enter the prompt for the extra label '{extra_name}'",
                    allow_empty=False,
                ).ask()

                extra_required = confirm(f"Is the extra label '{extra_name}' required").ask()
                extra_labels.append(
                    {
                        "name": extra_name,
                        "type": extra_type,
                        "description": extra_description,
                        "prompt": extra_prompt,
                        "required": extra_required,
                    }
                )

                console.print(f"Extra label '{extra_name}' added.", style="ctfa.success")
                console.print()  # Spacing

                if not confirm("Would you like to add another extra label").ask():
                    console.print()  # Spacing
                    break

            if not extra_labels:
                console.print(
                    "No extra labels were specified.\n",
                    style="ctfa.warning",
                )
                extra_labels = None
        else:
            console.print()  # Spacing
            extra_labels = None

    ctf_config = CTFConfig.model_validate(
        dict(
            name=name,
            flag_format=flag_format,
            starting_port=starting_port,
            categories=categories,
            difficulties=difficulties,
            extra_labels=extra_labels,
        )
    )
    console.print(CTFConfigComponent(ctf_config))

    if confirm("Is this information correct").ask():
        return ctf_config
    else:
        return None


def ask_challenge_details(  # noqa: C901
    config: CTFConfig, folder_name: str | None = None, gui: bool = True
) -> ChallengeConfig | None:
    import re

    from ctfa.cli.ui.components import ChallengeConfigComponent
    from ctfa.cli.ui.prompts import confirm, input_float, input_int, input_str, multiline_input, select
    from ctfa.models.challenge import ChallengeConfig
    from ctfa.utils import slugify

    challenge_id: str | None = None

    while True:
        name = input_str("Enter the challenge name", validator=lambda r: True if r else "Name cannot be empty").ask()

        if slugify(name) is None:
            if folder_name is not None and slugify(folder_name) is not None:
                console.print(
                    f"Using folder name '{folder_name}' as challenge ID.",
                    style="ctfa.info",
                )
                challenge_id = folder_name
                break

            console.print(
                "Unable to create valid challenge ID from the given name.",
                style="ctfa.warning",
            )

            if confirm(
                "Would you like to specify the challenge ID manually",
                yes_text="Yes, let me specify the challenge ID.",
                no_text="No, let me enter a different challenge name.",
            ):
                break
            else:
                continue
        else:
            challenge_id = slugify(name)
            assert challenge_id is not None

        break

    console.print()  # Spacing

    # Challenge ID
    if challenge_id is None or confirm("Would you like to specify the challenge ID manually").ask():

        def _validate_challenge_id(response: str) -> bool | str:
            if not response:
                return "Challenge ID cannot be empty."

            if not re.match(r"^[a-z][a-z0-9_-]*$", response):
                return "Challenge ID can only contain alphanumeric characters, hyphens, and underscores."

            return True

        challenge_id = input_str(
            "Enter the challenge ID",
            validator=_validate_challenge_id,
        ).ask()

        console.print()  # Spacing

    # Description
    description = multiline_input("Enter the challenge description").ask()
    console.print()  # Spacing

    # Category
    category: str = select(
        "Select the challenge category",
        choices=config.categories,
    ).ask()  # type: ignore
    console.print()  # Spacing

    difficulty: str = select(
        "Select the challenge difficulty",
        choices=config.difficulties,
    ).ask()  # type: ignore
    console.print()  # Spacing

    # Author
    author = input_str("Enter the challenge author").ask()
    console.print()  # Spacing

    # Extra labels
    extra_labels: dict[str, str | int | float | bool] = {}
    if config.extra_labels is not None:
        for extra_label in config.extra_labels:
            if (
                not extra_label.required
                and not confirm(f"Would you like to set the extra label '{extra_label.name}'").ask()
            ):
                continue

            if extra_label.type == "string":
                input_func = input_str
            elif extra_label.type == "integer":
                input_func = input_int
            elif extra_label.type == "float":
                input_func = input_float
            elif extra_label.type == "boolean":
                input_func = confirm
            else:
                console.print(
                    f"Warning: Unsupported extra label type '{extra_label.type}' for label '{extra_label.name}'. Skipping.",
                    style="ctfa.warning",
                )
                continue

            extra_labels[extra_label.name] = input_func(extra_label.prompt).ask()

            console.print()  # Spacing

    chall_config = ChallengeConfig(
        id=challenge_id,
        name=name,
        description=description,
        category=category,
        difficulty=difficulty,
        author=author,
        folder_name=folder_name or challenge_id,
        extra_labels=extra_labels or None,
    )
    console.print(ChallengeConfigComponent(chall_config))

    if confirm("Is this information correct").ask():
        return chall_config
    else:
        return None


# def ask_challenge_details(config: CTFConfig, gui: bool = True) -> ChallengeConfig | None:
#     _must_specify_challenge_id = False

#     import re
#     from textwrap import shorten

#     from ctfa.cli.ui.prompts import confirm, input_float, input_int, input_str, multi_select, multiline_input, select
#     from ctfa.utils import slugify

#     while True:
#         name = input_str("Enter the challenge name", validator=lambda r: True if r else "Name cannot be empty").ask()

#         if slugify(name) is None:
#             console.print(
#                 "Unable to create valid challenge ID from the given name.",
#                 style="ctfa.warning",
#             )

#             if confirm(
#                 "Would you like to specify the challenge ID manually",
#                 yes_text="Yes, let me specify the challenge ID.",
#                 no_text="No, let me enter a different challenge name.",
#             ):
#                 _must_specify_challenge_id = True
#                 break
#             else:
#                 continue

#         break

#     console.print()  # Spacing

#     # Challenge ID
#     if _must_specify_challenge_id or confirm("Would you like to specify the challenge ID manually").ask():

#         def _validate_challenge_id(response: str) -> bool | str:
#             if not response:
#                 return "Challenge ID cannot be empty."

#             if not re.match(r"^[a-z][a-z0-9_-]*$", response):
#                 return "Challenge ID can only contain alphanumeric characters, hyphens, and underscores."

#             return True

#         challenge_id = input_str(
#             "Enter the challenge ID",
#             validator=_validate_challenge_id,
#         ).ask()

#         console.print()  # Spacing
#     else:
#         challenge_id = slugify(name)
#         assert challenge_id is not None

#     # Description
#     description = multiline_input("Enter the challenge description").ask()
#     console.print()  # Spacing

#     # Category
#     category = select(
#         "Select the challenge category",
#         choices=config.categories,
#     ).ask()

#     difficulty = select(
#         "Select the challenge difficulty",
#         choices=config.difficulties,
#     ).ask()
#     console.print()  # Spacing

#     # Author
#     author = input_str("Enter the challenge author").ask()
#     console.print()  # Spacing

#     # Extra labels
#     extra_labels: dict[str, str | int | float | bool] = {}
#     if config.extra_labels is not None:
#         for extra_label in config.extra_labels:
#             if (
#                 not extra_label.required
#                 and not confirm(f"Would you like to set the extra label '{extra_label.name}'").ask()
#             ):
#                 continue

#             if extra_label.type == "string":
#                 input_func = input_str
#             elif extra_label.type == "integer":
#                 input_func = input_int
#             elif extra_label.type == "float":
#                 input_func = input_float
#             elif extra_label.type == "boolean":
#                 input_func = confirm
#             else:
#                 console.print(
#                     f"Warning: Unsupported extra label type '{extra_label.type}' for label '{extra_label.name}'. Skipping.",
#                     style="ctfa.warning",
#                 )
#                 continue

#             extra_labels[extra_label.name] = input_func(extra_label.prompt).ask()

#             console.print()  # Spacing

#     # Requirements
#     requirements: list[str] | None = None
#     if confirm("Would you like to add requirements for this challenge?").ask():
#         requirements = []
#         while True:
#             requirement: str | None = input_str(
#                 "Enter a requirement (leave empty to finish):",
#             ).ask()

#             if requirement is None or requirement.strip() == "":
#                 break

#             requirements.append(requirement.strip())
#             console.print()  # Spacing

#     console.print()  # Spacing

#     # Flags
#     flags = []

#     while True:
#         _flag_type = select(
#             "Select the flag type to add (or finish adding flags)",
#             choices=[
#                 "Static Flag",
#                 "Regex Flag",
#                 "Finish adding flags",
#             ],
#         ).ask()

#         if _flag_type == "Finish adding flags":
#             break

#         if _flag_type == "Static Flag":
#             _flag_value = input_str(
#                 "Enter the static flag value",
#                 validator=lambda r: True if r else "Flag value cannot be empty.",
#             ).ask()

#             _flag_case_sensitive = confirm("Is the flag case sensitive").ask()

#             flags.append(
#                 {
#                     "type": "static",
#                     "value": _flag_value,
#                     "case_sensitive": _flag_case_sensitive,
#                 }
#             )

#         elif _flag_type == "Regex Flag":
#             _flag_pattern = input_str(
#                 "Enter the regex flag pattern",
#                 validator=lambda r: True if r else "Flag pattern cannot be empty.",
#             ).ask()
#             flags.append(
#                 {
#                     "type": "regex",
#                     "pattern": _flag_pattern,
#                 }
#             )

#     if not flags:
#         console.print(
#             "Warning: No flags have been added to this challenge.",
#             style="ctfa.warning",
#         )
#         flags = None

#     console.print()  # Spacing

#     # Hints
#     hints: list[dict] | None = None
#     if confirm("Would you like to add hints for this challenge?").ask():
#         hints = []

#         while True:
#             _hint_content = input_str(
#                 "Enter a hint (leave empty to finish)",
#                 allow_empty=True,
#             ).ask()

#             if _hint_content.strip() == "":
#                 break

#             _hint_cost = input_int(
#                 "Enter the hint cost (points)",
#                 validator=lambda r: "Cost must be a positive integer." if r <= 0 else True,
#             ).ask()

#             if hints and confirm("Does this hint require a previous hint to be unlocked").ask():
#                 _hint_requirements = multi_select(
#                     "Select the prerequisite hints:",
#                     choices=[
#                         shorten(
#                             " ".join(h["content"].splitlines()),
#                             width=50,
#                             placeholder="...",
#                         )
#                         for h in hints
#                     ],
#                     return_indices=True,
#                 ).ask()
#             else:
#                 _hint_requirements = None

#             hints.append(
#                 {
#                     "content": _hint_content.strip(),
#                     "cost": int(_hint_cost),
#                     "requirements": _hint_requirements,
#                 }
#             )
#             console.print()  # Spacing

#     console.print()  # Spacing

#     # Distribution files

#     # Source files

#     # Solution files

#     # Services


if __name__ == "__main__":
    ctf_config = ask_ctf_config()
    if ctf_config is not None:
        ask_challenge_details(ctf_config)
