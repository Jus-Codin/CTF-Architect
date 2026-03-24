from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from typing import Annotated, Literal

from cyclopts import App, Parameter

from ctfa.cli.param_types import ResolvedExistingChallengeFolder

app = App(
    name="flag",
    group="Challenge Flag Commands",
    help="Commands for managing challenge flags",
)

FlagType = Literal["static", "regex"]


def _format_flag(flag: object, index: int | None = None) -> str:
    from ctfa.models.challenge import RegexFlag, StaticFlag

    if isinstance(flag, StaticFlag):
        sensitivity = "case-sensitive" if flag.case_sensitive else "case-insensitive"
        value = shorten(flag.value, width=60, placeholder="...")
        label = f"static: {value} ({sensitivity})"
    elif isinstance(flag, RegexFlag):
        pattern = shorten(flag.pattern, width=60, placeholder="...")
        label = f"regex: {pattern}"
    else:
        label = "unknown flag"

    if index is None:
        return label
    return f"{index}. {label}"


def _select_flag_index(flags: list[object]) -> int:
    from ctfa.cli.ui.prompts import select

    choices = [_format_flag(flag, i + 1) for i, flag in enumerate(flags)]
    return int(select("Select the flag", choices=choices, return_index=True).ask())


def _select_flag_type(current: FlagType | None = None) -> FlagType:
    from ctfa.cli.ui.prompts import select

    if current is None:
        choices = ["static", "regex"]
    else:
        choices = [current, "regex" if current == "static" else "static"]

    return select("Select the flag type", choices=choices).ask()  # type: ignore[return-value]


def _select_case_sensitivity(current: bool | None = None) -> bool:
    from ctfa.cli.ui.prompts import select

    if current is None:
        choices = ["Case sensitive", "Case insensitive"]
    elif current:
        choices = ["Case sensitive", "Case insensitive"]
    else:
        choices = ["Case insensitive", "Case sensitive"]

    selected = select("Select case sensitivity", choices=choices).ask()
    return selected == "Case sensitive"


def add_command(
    flag_type: Annotated[FlagType | None, Parameter(name=["--type", "-t"])] = None,
    value: Annotated[str | None, Parameter(name=["--value", "-v"])] = None,
    pattern: Annotated[str | None, Parameter(name=["--pattern"])] = None,
    case_sensitive: Annotated[bool | None, Parameter(name=["--case-sensitive"], negative="--case-insensitive")] = None,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
    *,
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
):
    """Add a flag to a challenge folder.

    Args:
        flag_type (FlagType | None, optional): The flag type to add ("static" or "regex")
        value (str | None, optional): The static flag value
        pattern (str | None, optional): The regex flag pattern
        case_sensitive (bool | None, optional): Whether the static flag is case-sensitive
        no_interactive (bool, optional): Disable interactive prompts
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
    """
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.prompts import input_str
    from ctfa.core.challenge import Challenge
    from ctfa.models.challenge import RegexFlag, StaticFlag

    chall = Challenge.load_folder(challenge_path)
    flags = list(chall.config.flags or [])

    if flag_type is None:
        if no_interactive:
            console.print("Flag type is required when --no-interactive is set.", style="ctfa.error")
            return
        flag_type = _select_flag_type()

    if flag_type == "static":
        if value is None:
            if no_interactive:
                console.print("Static flag value is required when --no-interactive is set.", style="ctfa.error")
                return
            value = input_str("Enter the static flag value", allow_empty=False).ask()

        if case_sensitive is None:
            if no_interactive:
                case_sensitive = True
            else:
                case_sensitive = _select_case_sensitivity()

        flags.append(StaticFlag(value=value, case_sensitive=case_sensitive))
    else:
        if pattern is None:
            if no_interactive:
                console.print("Regex flag pattern is required when --no-interactive is set.", style="ctfa.error")
                return
            pattern = input_str("Enter the regex flag pattern", allow_empty=False).ask()

        flags.append(RegexFlag(pattern=pattern))

    chall.config.flags = flags
    chall.save()

    console.print("Flag added successfully.", style="ctfa.success")


def edit_command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    index: Annotated[int | None, Parameter(name=["--index", "-i"])] = None,
    flag_type: Annotated[FlagType | None, Parameter(name=["--type", "-t"])] = None,
    value: Annotated[str | None, Parameter(name=["--value", "-v"])] = None,
    pattern: Annotated[str | None, Parameter(name=["--pattern"])] = None,
    case_sensitive: Annotated[bool | None, Parameter(name=["--case-sensitive"], negative="--case-insensitive")] = None,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Edit a flag in a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
        index (int | None, optional): The 1-based index of the flag to edit
        flag_type (FlagType | None, optional): The new flag type ("static" or "regex")
        value (str | None, optional): The new static flag value
        pattern (str | None, optional): The new regex flag pattern
        case_sensitive (bool | None, optional): Whether the static flag is case-sensitive
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.console import console
    from ctfa.cli.ui.prompts import input_str
    from ctfa.core.challenge import Challenge
    from ctfa.models.challenge import RegexFlag, StaticFlag

    chall = Challenge.load_folder(challenge_path)
    flags = list(chall.config.flags or [])

    if not flags:
        console.print("No flags are currently defined for this challenge.", style="ctfa.warning")
        return

    if index is None:
        if no_interactive:
            console.print("Flag index is required when --no-interactive is set.", style="ctfa.error")
            return
        flag_index = _select_flag_index(flags)
    else:
        if index < 1 or index > len(flags):
            console.print("Flag index is out of range.", style="ctfa.error")
            return
        flag_index = index - 1

    current_flag = flags[flag_index]
    current_type: FlagType
    if isinstance(current_flag, StaticFlag):
        current_type = "static"
    else:
        current_type = "regex"

    if flag_type is None:
        if no_interactive:
            flag_type = current_type
        else:
            flag_type = _select_flag_type(current=current_type)

    if flag_type == "static":
        if value is None:
            if no_interactive:
                value = current_flag.value if isinstance(current_flag, StaticFlag) else None
                if value is None:
                    console.print("Static flag value is required when --no-interactive is set.", style="ctfa.error")
                    return
            else:
                default_value = current_flag.value if isinstance(current_flag, StaticFlag) else ""
                value = input_str("Enter the static flag value", default=default_value, allow_empty=False).ask()

        if case_sensitive is None:
            if no_interactive:
                case_sensitive = current_flag.case_sensitive if isinstance(current_flag, StaticFlag) else True
            else:
                current = current_flag.case_sensitive if isinstance(current_flag, StaticFlag) else None
                case_sensitive = _select_case_sensitivity(current=current)

        flags[flag_index] = StaticFlag(value=value, case_sensitive=case_sensitive)
    else:
        if pattern is None:
            if no_interactive:
                pattern = current_flag.pattern if isinstance(current_flag, RegexFlag) else None
                if pattern is None:
                    console.print("Regex flag pattern is required when --no-interactive is set.", style="ctfa.error")
                    return
            else:
                default_pattern = current_flag.pattern if isinstance(current_flag, RegexFlag) else ""
                pattern = input_str("Enter the regex flag pattern", default=default_pattern, allow_empty=False).ask()

        flags[flag_index] = RegexFlag(pattern=pattern)

    chall.config.flags = flags
    chall.save()

    console.print("Flag updated successfully.", style="ctfa.success")


def remove_command(
    challenge_path: Annotated[ResolvedExistingChallengeFolder, Parameter(name=["--path", "-p"])] = Path.cwd(),
    *,
    index: Annotated[int | None, Parameter(name=["--index", "-i"])] = None,
    no_interactive: Annotated[bool, Parameter(name=["--no-interactive"], negative="")] = False,
):
    """Remove a flag from a challenge folder.

    Args:
        challenge_path (ResolvedExistingChallengeFolder, optional): The path to the challenge folder to edit
        index (int | None, optional): The 1-based index of the flag to remove
        no_interactive (bool, optional): Disable interactive prompts
    """
    from ctfa.cli.ui.console import console
    from ctfa.core.challenge import Challenge

    chall = Challenge.load_folder(challenge_path)
    flags = list(chall.config.flags or [])

    if not flags:
        console.print("No flags are currently defined for this challenge.", style="ctfa.warning")
        return

    if index is None:
        if no_interactive:
            console.print("Flag index is required when --no-interactive is set.", style="ctfa.error")
            return
        flag_index = _select_flag_index(flags)
    else:
        if index < 1 or index > len(flags):
            console.print("Flag index is out of range.", style="ctfa.error")
            return
        flag_index = index - 1

    removed_flag = flags.pop(flag_index)
    chall.config.flags = flags or None
    chall.save()

    console.print(f"Removed {_format_flag(removed_flag)}.", style="ctfa.success")


app.command(add_command, name="add")
app.command(edit_command, name="edit")
app.command(remove_command, name="remove", alias="rm")
