from __future__ import annotations

from ast import literal_eval
from pathlib import Path

from readchar import key as _key
from readchar import readkey
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.style import Style
from rich.text import Text
from typer import Exit

from ctf_architect._console import console
from ctf_architect.chall_architect.core.utils import (
    get_config,
    valid_challenge_folder_name,
    valid_service_folder,
    valid_service_name,
)
from ctf_architect.core.models import CTFConfig, Flag, Hint, Service

DEFAULT_HEADER_STYLE = Style(color="green")
DEFAULT_PREFIX_STYLE = Style(color="bright_black")
DEFAULT_CURSOR_STYLE = Style(color="cyan", blink=True)
DEFUALT_SELECTED_STYLE = Style(color="bright_cyan", bold=True)
DEFAULT_TOGGLED_STYLE = Style(color="bright_green")
DEFAULT_UNTOGGLED_STYLE = Style(color="bright_black")
DEFAULT_INPUT_STYLE = Style(color="cyan")
DEFAULT_SELECTOR = Text("\u276f", style=DEFUALT_SELECTED_STYLE)
NEWLINE_RESET = Text("\n", style="reset")


# There's probably a super fancy and sophisticated way to do this for all
# PromptBase classes, but I couldn't be bothered right now
def prompt(message: str, **kwargs) -> str:
    message = Text.from_markup(message, style=DEFAULT_HEADER_STYLE)

    return Prompt.ask(message, console=console, **kwargs)


def prompt_int(message: str, **kwargs) -> int:
    message = Text.from_markup(message, style=DEFAULT_HEADER_STYLE)

    return IntPrompt.ask(message, console=console, **kwargs)


def confirm(message: str, **kwargs) -> bool:
    message = Text.from_markup(message, style=DEFAULT_HEADER_STYLE)

    return Confirm.ask(message, console=console, **kwargs)


def ask_abort(
    message: str | Text = "Are you sure you want to abort?",
    abort_message: str | Text = "Aborting...",
) -> None:
    if confirm(message, default=False):
        console.print(abort_message, style="red")
        raise Exit(1)


def ask_multiline_input(
    message: str | Text | None = None,
    line_prefix: str | Text = ">>> ",
    transient: bool = False,
    header_style: str | Style = DEFAULT_HEADER_STYLE,
    prefix_style: str | Style = DEFAULT_PREFIX_STYLE,
    text_style: str | Style = DEFAULT_INPUT_STYLE,
) -> str:
    input_str = ""

    helper_text = Text(
        "Press ENTER to add a line, or ESC (or CTRL+D) to finish", style=header_style
    )

    if message is not None:
        if isinstance(message, str):
            message = Text.from_markup(message, style=header_style)

        if not message.plain.endswith(":"):
            message.append(":")

        header = (
            message.copy()
            .append("\n")
            .append_text(helper_text)
            .append_text(NEWLINE_RESET)
        )
    else:
        header = helper_text.copy().append_text(NEWLINE_RESET)

    def _show_text() -> Text:
        text = header.copy()

        text += Text("\n").join(
            Text(line_prefix, style=prefix_style) + Text(line, style=text_style)
            for line in input_str.split("\n")
        )

        return text

    with Live(
        _show_text(),
        console=console,
        auto_refresh=False,
        transient=transient,
    ) as live:
        while True:
            key = readkey()

            # readkey cannot detect ESC on POSIX systems, so we need to check for CTRL+D
            # See: https://github.com/magmax/python-readchar/issues/94
            if key == _key.ESC or key == _key.CTRL_D:
                live.stop()
                break
            elif key == _key.BACKSPACE:
                input_str = input_str[:-1]
            elif key == _key.ENTER:
                input_str += "\n"
            else:
                input_str += key
            live.update(_show_text(), refresh=True)

    return input_str


def ask_choice(
    choices: list[str],
    message: str | Text | None = None,
    return_index: bool = False,
    indent: int = 2,
    transient: bool = False,
    header_style: str | Style = DEFAULT_HEADER_STYLE,
    selected_style: str | Style = DEFUALT_SELECTED_STYLE,
    unselected_style: str | Style = DEFAULT_INPUT_STYLE,
    selector: str = DEFAULT_SELECTOR,
    selector_style: str | Style = DEFUALT_SELECTED_STYLE,
) -> str | int:
    helper_text = Text(
        "Use arrow keys (↑/↓) or j/k to move and press Enter to select",
        style=header_style,
    )

    if message is not None:
        if isinstance(message, str):
            message = Text.from_markup(message, style=header_style)

        if not message.plain.endswith(":"):
            message.append(":")

        header = (
            message.copy()
            .append("\n")
            .append_text(helper_text)
            .append_text(NEWLINE_RESET)
        )
    else:
        message = Text("Answer:", style=header_style)
        header = helper_text.copy().append_text(NEWLINE_RESET)

    indent_str = " " * indent

    def _show_choices(selected_index: int, final: bool = False) -> Text:
        if final:
            choices_text = message.copy()
            choices_text.append(f" {choices[selected_index]}", style=selected_style)
            return choices_text
        else:
            choices_text = header.copy()

            for i, choice in enumerate(choices):
                if i == selected_index:
                    choices_text.append(
                        f"{indent_str}{selector} ", style=selector_style
                    )
                    choices_text.append(choice, style=selected_style)
                else:
                    choices_text.append(
                        f"{indent_str}  {choice}", style=unselected_style
                    )

                choices_text.append("\n")

            return choices_text

    selected_index = 0

    with Live(
        _show_choices(selected_index),
        console=console,
        auto_refresh=False,
        transient=transient,
    ) as live:
        while True:
            key = readkey()

            if key == _key.UP or key == "k":
                selected_index = max(0, selected_index - 1)
            elif key == _key.DOWN or key == "j":
                selected_index = min(len(choices) - 1, selected_index + 1)
            elif key == _key.ENTER:
                live.update(_show_choices(selected_index, final=True), refresh=True)
                live.stop()
                break

            live.update(_show_choices(selected_index), refresh=True)

    return selected_index if return_index else choices[selected_index]


def ask_checkbox(
    choices: list[str],
    message: str | Text | None = None,
    return_indexes: bool = False,
    indent: int = 2,
    transient: bool = False,
    header_style: str | Style = DEFAULT_HEADER_STYLE,
    toggled_symbol: str = "\u2611",
    untoggled_symbol: str = "\u2610",
    toggled_style: str | Style = DEFAULT_TOGGLED_STYLE,
    untoggled_style: str | Style = DEFAULT_UNTOGGLED_STYLE,
    selected_style: str | Style = DEFUALT_SELECTED_STYLE,
    unselected_style: str | Style = DEFAULT_INPUT_STYLE,
    selector: str = DEFAULT_SELECTOR,
    selector_style: str | Style = DEFUALT_SELECTED_STYLE,
) -> list[str | int]:
    helper_text = Text(
        "Use arrow keys (↑/↓) or j/k to move, press Space to toggle and Enter to submit",
        style=header_style,
    )

    if message is not None:
        if isinstance(message, str):
            message = Text.from_markup(message, style=header_style)

        if not message.plain.endswith(":"):
            message.append(":")

        header = (
            message.copy()
            .append("\n")
            .append_text(helper_text)
            .append_text(NEWLINE_RESET)
        )
    else:
        header = helper_text.copy().append_text(NEWLINE_RESET)

    indent_str = " " * indent

    states = [[choice, False] for choice in choices]

    def _show_choices(selected_index: int) -> Text:
        choices_text = header.copy()

        for i, (choice, toggled) in enumerate(states):
            symbol = toggled_symbol if toggled else untoggled_symbol
            symbol_style = toggled_style if toggled else untoggled_style

            if i == selected_index:
                choices_text.append(f"{indent_str}{selector} ", style=selector_style)
                choices_text.append(f"{symbol} ", style=symbol_style)
                choices_text.append(choice, style=selected_style)
            else:
                choices_text.append(f"{indent_str}  {symbol} ", style=symbol_style)
                choices_text.append(choice, style=unselected_style)

            choices_text.append("\n")

        return choices_text

    selected_index = 0

    with Live(
        _show_choices(selected_index),
        console=console,
        auto_refresh=False,
        transient=transient,
    ) as live:
        while True:
            key = readkey()

            if key == _key.UP or key == "k":
                selected_index = max(0, selected_index - 1)
            elif key == _key.DOWN or key == "j":
                selected_index = min(len(choices) - 1, selected_index + 1)
            elif key == _key.SPACE:
                states[selected_index][1] = not states[selected_index][1]
            elif key == _key.ENTER:
                live.stop()
                break

            live.update(_show_choices(selected_index), refresh=True)

    return [
        i if return_indexes else choice
        for i, (choice, toggled) in enumerate(states)
        if toggled
    ]


def ask_ctf_config(no_gui: bool, path: Path | None = None) -> CTFConfig:
    if path is None:
        if no_gui:
            while True:
                try:
                    path_string = prompt("Enter the path to the CTF config file")
                except KeyboardInterrupt:
                    # User cancelled the prompt, abort
                    ask_abort()
                    continue

                if not path_string:
                    console.print(":x: Path cannot be empty", style="red")
                    continue

                config_path = Path(path_string)

                if not config_path.exists():
                    console.print(":x: Path does not exist", style="red")
                    continue

                if not config_path.is_file():
                    console.print(":x: Path is not a file", style="red")
                    continue

                break

        else:
            from tkinter.filedialog import askopenfilename

            while True:
                console.print("Please select the CTF config file.", style="cyan")

                path_string = askopenfilename(
                    title="Select the CTF config file",
                    filetypes=[("TOML files", "*.toml")],
                )

                if path_string == "":
                    # User cancelled the dialog, abort
                    ask_abort()
                    continue

                config_path = Path(path_string)
                break
    else:
        config_path = path

    try:
        config = get_config(config_path)
    except Exception as e:
        console.print(f":x: Error reading the config file: {e}", style="red")
        return

    config_string = "[cyan][bright_cyan]Categories:[/bright_cyan]"
    for category in config.categories:
        config_string += f"\n  - {category.capitalize()}"

    config_string += "\n\n[bright_cyan]Difficulties:[/bright_cyan]"
    for difficulty in config.difficulties:
        config_string += f"\n  - {difficulty.name.capitalize()} ({difficulty.value})"

    config_string += "\n\n[bright_cyan]Extra Fields:[/bright_cyan]"
    if not config.extras:
        config_string += "\n  None"
    else:
        for extra in config.extras:
            config_string += f"\n  - {extra}"

    config_string += (
        f"\n\n[bright_cyan]Starting Port:[/bright_cyan] {config.starting_port}[/cyan]"
    )

    console.print(
        Panel(
            config_string,
            title=f"[bold yellow]{config.name} Config[bold yellow]",
            border_style="blue",
        )
    )

    if confirm("Is this the correct config?"):
        return config
    elif path is not None:
        return ask_ctf_config(no_gui)
    else:
        console.print("Aborting...", style="red")
        raise Exit(1)


def ask_challenge_name() -> str:
    while True:
        try:
            name = prompt(":rocket: Enter the name of the challenge")
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if not name:
            console.print(":x: Name cannot be empty", style="red")
            continue

        return name


def ask_challenge_description() -> str:
    while True:
        try:
            return ask_multiline_input(
                ":rocket: Enter the description of the challenge"
            )
        except KeyboardInterrupt:
            ask_abort()


def ask_challenge_difficulty(config: CTFConfig) -> str:
    while True:
        try:
            index = ask_choice(
                [f"{d.name.capitalize()} ({d.value})" for d in config.difficulties],
                ":rocket: Select the difficulty of the challenge",
                return_index=True,
            )
            return config.difficulties[index].name.capitalize()
        except KeyboardInterrupt:
            ask_abort()


def ask_challenge_category(config: CTFConfig) -> str:
    while True:
        try:
            return ask_choice(
                [c.capitalize() for c in config.categories],
                ":rocket: Select the category of the challenge",
            )
        except KeyboardInterrupt:
            ask_abort()


def ask_challenge_author() -> str:
    while True:
        try:
            author = prompt(":rocket: Enter the author of the challenge")
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if not author:
            console.print(":x: Author cannot be empty", style="red")
            continue

        return author


def ask_folder_name() -> str:
    while True:
        try:
            name = prompt(":rocket: Enter the name of the folder")
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if not name:
            console.print(":x: Name cannot be empty", style="red")
            continue

        if not valid_challenge_folder_name(name):
            console.print(":x: Invalid folder name", style="red")
            continue

        return name


def ask_challenge_extras(config: CTFConfig) -> dict[str, str]:
    extras = {}

    for extra in config.extras:
        while True:
            try:
                value = prompt(f"Enter the value for the extra field '{extra}'")
            except KeyboardInterrupt:
                # User cancelled the prompt, abort
                ask_abort()
                continue

            if not value:
                console.print(":x: Value cannot be empty", style="red")
                continue

            extras[extra] = value
            break

    return extras


def ask_challenge_requirements() -> list[str]:
    requirements = []

    while True:
        try:
            requirement = prompt(
                "Enter a requirement to unlock the challenge (leave empty to finish)"
            )
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if not requirement:
            if len(requirements) > 0 or confirm(
                "Are you sure you want to finish without adding any requirements?"
            ):
                return requirements
            else:
                continue

        requirements.append(requirement)


def ask_source_files(no_gui: bool) -> list[Path]:
    if no_gui:
        paths = []

        while True:
            try:
                path = prompt("Enter the path to a source file (leave empty to finish)")
            except KeyboardInterrupt:
                # User cancelled the prompt, abort
                ask_abort()
                continue

            if not path:
                if len(paths) > 0 or confirm(
                    "Are you sure you want to finish without adding any files?"
                ):
                    return paths
                else:
                    continue

            path = Path(path)

            if not path.exists():
                console.print(":x: Path does not exist", style="red")
                continue

            if not path.is_file():
                console.print(":x: Path is not a file", style="red")
                continue

            paths.append(path)
    else:
        from tkinter.filedialog import askopenfilenames

        while True:
            console.print(
                ":file_folder: Please select the source files for the challenge.",
                style="cyan",
            )

            paths = askopenfilenames(title="Select the source files for the challenge")

            if paths == "":
                # User cancelled the dialog, abort
                ask_abort()
                continue

            _paths = []

            console.print(
                f"Selected {len(paths)} source file{'s' if len(paths) > 1 else ''}.",
                style="cyan",
            )

            for path in paths:
                path = Path(path)
                console.print(f"  - {path}", style="cyan")
                _paths.append(path)

            return _paths


def ask_solution_files(no_gui: bool) -> list[Path]:
    if no_gui:
        paths = []

        while True:
            try:
                path = prompt(
                    "Enter the path to a solution file (leave empty to finish)"
                )
            except KeyboardInterrupt:
                # User cancelled the prompt, abort
                ask_abort()
                continue

            if not path:
                if len(paths) > 0 or confirm(
                    "Are you sure you want to finish without adding any files?"
                ):
                    return paths
                else:
                    continue

            path = Path(path)

            if not path.exists():
                console.print(":x: Path does not exist", style="red")
                continue

            if not path.is_file():
                console.print(":x: Path is not a file", style="red")
                continue

            paths.append(path)

    else:
        from tkinter.filedialog import askopenfilenames

        while True:
            console.print(
                ":file_folder: Please select the solution files for the challenge."
            )

            paths = askopenfilenames(
                title="Select the solution files for the challenge"
            )

            if paths == "":
                # User cancelled the dialog, abort
                ask_abort()
                continue

            _paths = []

            console.print(
                f"Selected {len(paths)} solution file{'s' if len(paths) > 1 else ''}."
            )

            for path in paths:
                path = Path(path)
                console.print(f"  - {path}")
                _paths.append(path)

            return _paths


def ask_challenge_files(no_gui: bool) -> list[Path | str]:
    files = []

    while True:
        try:
            file_type = ask_choice(
                ["Local File", "Remote File", "Finish"],
                ":rocket: Select the type of files to add",
                transient=True,
            )
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if file_type == "Finish":
            if len(files) > 0 or confirm(
                "Are you sure you want to finish without adding any files?"
            ):
                return files
            else:
                continue

        elif file_type == "Local File":
            if no_gui:
                while True:
                    try:
                        path = prompt(
                            "Enter the path to a file to add to the challenge"
                        )
                    except KeyboardInterrupt:
                        # User cancelled the prompt, we return back to the file type selection
                        # This one is a bit different because there is an option to finish
                        break

                    if not path:
                        console.print(":x: Path cannot be empty", style="red")
                        continue

                    path = Path(path)

                    if not path.exists():
                        console.print(":x: Path does not exist", style="red")
                        continue

                    if not path.is_file():
                        console.print(":x: Path is not a file", style="red")
                        continue

                    files.append(path)
                    break
            else:
                from tkinter.filedialog import askopenfilenames

                console.print(
                    ":file_folder: Please select the files to add to the challenge.",
                    style="cyan",
                )

                paths = askopenfilenames(
                    title="Select the files to add to the challenge"
                )

                if paths == "":
                    # User cancelled the dialog, we return back to the file type selection
                    # This one is a bit different because there is an option to finish
                    continue

                _paths = []

                console.print(
                    f"Selected {len(paths)} file{'s' if len(paths) > 1 else ''}.",
                    style="cyan",
                )

                for path in paths:
                    path = Path(path)
                    console.print(f"  - {path}", style="cyan")
                    _paths.append(path)

                files.extend(_paths)

        elif file_type == "Remote File":
            while True:
                try:
                    url = prompt("Enter the URL of the remote file")
                except KeyboardInterrupt:
                    # User cancelled the prompt, we return back to the file type selection
                    # This one is a bit different because there is an option to finish
                    break

                if not url:
                    console.print(":x: URL cannot be empty", style="red")
                    continue

                # LIMITATION: We don't check if the URL is valid

                files.append(url)
                break


def ask_flags() -> list[Flag]:
    flags = []

    while True:
        try:
            flag_type = ask_choice(
                ["Static", "Regex", "Finish"],
                ":triangular_flag: Select the type of flag to add",
                transient=True,
            )
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if flag_type == "Finish":
            if len(flags) > 0 or confirm(
                "Are you sure you want to finish without adding any flags?"
            ):
                return flags
            else:
                continue

        try:
            case_sensitive = confirm("Is the flag case sensitive?")
        except KeyboardInterrupt:
            # User cancelled the prompt, we return back to the flag type selection
            continue

        while True:
            flag_str = prompt(":triangular_flag: Enter the flag")

            if flag_str:
                break

            console.print(":x: Flag cannot be empty", style="red")
            continue

        flag = Flag(
            flag=flag_str,
            regex=flag_type == "Regex",
            case_sensitive=case_sensitive,
        )

        flags.append(flag)


def ask_hints(hints: list[str] | None = None) -> list[Hint]:
    _hints: list[Hint] = []

    if hints is None:
        prompt_for_hints = True
    else:
        prompt_for_hints = False
        hints = hints[::-1]

    while True:
        if prompt_for_hints:
            try:
                hint_str = ask_multiline_input(
                    ":bulb: Enter the content of the hint",
                    transient=True,
                )
            except KeyboardInterrupt:
                # User cancelled the prompt, abort
                ask_abort()
                continue
        else:
            if len(hints) == 0:
                return _hints
            hint_str = hints.pop()

        if not hint_str:
            console.print(":x: Hint cannot be empty", style="red")
            continue

        value = prompt_int(":bulb: Enter the cost of the hint")

        if len(_hints) > 0 and confirm("Do you want to add requirements to this hint?"):
            requirements = ask_checkbox(
                [hint if len(hint) <= 20 else f"{hint[:17]}..." for hint in _hints],
                ":bulb: Select the requirements to unlock this hint",
                return_indexes=True,
                transient=True,
            )
        else:
            requirements = None

        hint = Hint(cost=value, content=hint_str, requirements=requirements)

        _hints.append(hint)

        # Ask if the user wants to add another hint
        if prompt_for_hints and not confirm("Do you want to add another hint?"):
            return _hints


def ask_services(
    no_gui: bool, service_paths: list[Path] | None = None
) -> list[Service]:
    services = []

    if service_paths is None:
        prompt_for_services = True
        choices = ["Web", "Netcat", "SSH", "Secret", "Internal", "Finish"]
    else:
        prompt_for_services = False
        choices = ["Web", "Netcat", "SSH", "Secret", "Internal"]
        service_paths = service_paths[::-1]

    while True:
        if not prompt_for_services:
            if len(service_paths) == 0:
                return services

            path = service_paths.pop()

            if not path.exists():
                console.print(":x: Path does not exist", style="red")
                continue

            if not path.is_dir():
                console.print(":x: Path is not a folder", style="red")
                continue

            if not valid_service_folder(path):
                console.print(":x: Invalid service folder", style="red")
                continue

            console.print(
                f':file_folder: Configure service for "{path}"', style="bright_cyan"
            )

        try:
            service_type = ask_choice(
                choices,
                ":computer: Select the type of service to add",
                transient=True,
            )
        except KeyboardInterrupt:
            # User cancelled the prompt, abort
            ask_abort()
            continue

        if service_type == "Finish":
            if len(services) > 0 or confirm(
                "Are you sure you want to finish without adding any services?"
            ):
                return services
            else:
                continue

        while True:
            try:
                name = prompt(":computer: Enter the name of the service")
            except KeyboardInterrupt:
                # User cancelled the prompt, abort
                ask_abort()
                continue

            if not name:
                console.print(":x: Name cannot be empty", style="red")
                continue

            if not valid_service_name(name):
                console.print(":x: Invalid service name", style="red")
                continue

            break

        if service_type == "Internal" and not confirm(
            ":computer: Do you want to specify ports for this service?"
        ):
            ports = None
        else:
            ports = []

            while True:
                try:
                    port = prompt_int(":computer: Enter a port for the service")
                except KeyboardInterrupt:
                    # User cancelled the prompt, abort
                    ask_abort()
                    continue

                if port < 1 or port > 65535:
                    console.print(":x: Port must be between 1 and 65535", style="red")
                    continue

                if port in ports:
                    console.print(":x: Port already specified", style="red")
                    continue

                ports.append(port)

                if not confirm("Do you want to add another port?"):
                    break

        if prompt_for_services:
            if no_gui:
                while True:
                    try:
                        path = prompt(
                            "Enter the path to the service folder (leave empty to finish)"
                        )
                    except KeyboardInterrupt:
                        # User cancelled the prompt, abort
                        ask_abort()
                        continue

                    if not path:
                        console.print(":x: Path cannot be empty", style="red")
                        continue

                    path = Path(path)

                    if not path.exists():
                        console.print(":x: Path does not exist", style="red")
                        continue

                    if not path.is_dir():
                        console.print(":x: Path is not a folder", style="red")
                        continue

                    if not valid_service_folder(path):
                        console.print(":x: Invalid service folder", style="red")
                        continue

                    break
            else:
                from tkinter.filedialog import askdirectory

                while True:
                    console.print(
                        ":file_folder: Please select the service folder.", style="cyan"
                    )

                    path = askdirectory(title="Select the service folder")

                    if path == "":
                        # User cancelled the dialog, abort
                        ask_abort()
                        continue

                    path = Path(path)

                    if valid_service_folder(path):
                        console.print(":x: Invalid service folder", style="red")
                        continue

                    console.print(
                        f':file_folder: Selected service folder: "{path}"', style="cyan"
                    )

                    break

        if confirm(":computer: Does the service have any extra fields?", default=False):
            extras = {}

            while True:
                try:
                    key = prompt(":computer: Enter the key of the extra field")
                except KeyboardInterrupt:
                    # User cancelled the prompt, abort
                    ask_abort()
                    continue

                if not key:
                    console.print(":x: Key cannot be empty", style="red")
                    continue

                while True:
                    try:
                        # This could be dangerous. While RCE should not be possible,
                        # it is still possible to crash the interpreter with this.
                        value = literal_eval(
                            prompt(
                                ":computer: Enter the value of the extra field as a Python literal (e.g. 'True', '\"Hello\"', '42')"
                            )
                        )
                    except KeyboardInterrupt:
                        # User cancelled the prompt, abort
                        ask_abort()
                        continue
                    except Exception as e:
                        console.print(f":x: Error parsing value: {e}", style="red")
                        continue

                    extras[key] = value
                    break

        else:
            extras = None

        service = Service(
            name=name,
            path=path,
            ports=ports,
            type=service_type.lower(),
            extras=extras,
        )

        services.append(service)
