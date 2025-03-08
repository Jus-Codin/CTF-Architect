from __future__ import annotations

from typing import Generic, TypeVar, cast

from readchar import key as _key
from readchar import readkey
from rich.console import Console
from rich.live import Live
from rich.text import Text, TextType

from ctf_architect.cli.ui.prompts.base import PromptBase
from ctf_architect.cli.ui.prompts.session import PromptSession

SelectType = TypeVar("SelectType")


NEWLINE_RESET = Text("\n", style="reset")


class Select(PromptBase, Generic[SelectType]):
    helper_text = "Use arrow keys (↑/↓) or k/j to move and press Enter to select"
    prompt_pointer = "\u276f "

    def __init__(
        self,
        choices: list[SelectType],
        prompt: TextType = "",
        return_index: bool = False,
        *,
        console: Console | None = None,
        indent: int = 2,
        transient: bool = False,
        prompt_suffix: str = ":",
    ):
        self.choices = choices
        self.return_index = return_index
        self.indent = indent
        self.transient = transient
        self.prompt_suffix = prompt_suffix
        super().__init__(prompt, console=console)

    def render_choices(self, selected_index: int) -> TextType:
        if self.prompt.plain:
            # choices_text = (
            #     self.prompt.copy()
            #     .append(self.prompt_suffix)
            #     .append("\n")
            #     .append(self.helper_text, style="ctfa.prompt.message")
            #     .append_text(NEWLINE_RESET)
            # )
            choices_text = (
                Text(self.helper_text, style="ctfa.prompt.message")
                .append("\n")
                .append_text(self.prompt.copy())
                .append(self.prompt_suffix)
                .append_text(NEWLINE_RESET)
            )
        else:
            choices_text = Text(self.helper_text, style="ctfa.prompt.message").append_text(NEWLINE_RESET)

        indent_str = " " * self.indent

        for i, choice in enumerate(self.choices):
            if i == selected_index:
                choices_text.append(f"{indent_str}{self.prompt_pointer}", style="ctfa.prompt.pointer")
                choices_text.append(f"{choice}", style="ctfa.prompt.selected")
            else:
                choices_text.append(f"{indent_str}  {choice}", style="ctfa.prompt.unselected")

            choices_text.append("\n")

        return choices_text

    def render_result(self, selected_index: int) -> TextType:
        if self.prompt.plain:
            result_text = self.prompt.copy().append(self.prompt_suffix)
        else:
            result_text = Text("Answer:", style="ctfa.prompt.message")

        result_text.append(f" {self.choices[selected_index]}", style="ctfa.prompt.selected")
        return result_text

    def make_prompt(self, session: PromptSession) -> TextType:
        if "selected_index" not in session.state:
            session.state["selected_index"] = 0

        selected_index = session.state["selected_index"]
        return self.render_choices(selected_index)

    def get_input(self, session: PromptSession, prompt: TextType | None = None) -> SelectType | int:
        # session.live will always be set if this method is called
        live = cast(Live, session.live)

        while True:
            selected_index: int = session.state.get("selected_index", 0)

            key = readkey()

            if key == _key.UP or key == "k":
                selected_index = max(0, selected_index - 1)
            elif key == _key.DOWN or key == "j":
                selected_index = min(len(self.choices) - 1, selected_index + 1)
            elif key == _key.ENTER:
                live.update(self.render_result(selected_index), refresh=True)
                live.stop()
                break

            live.update(self.render_choices(selected_index), refresh=True)

            session.state["selected_index"] = selected_index

        return selected_index if self.return_index else self.choices[selected_index]

    def process_response(self, session: PromptSession, response: SelectType | int) -> SelectType | int:
        return response

    def execute(self, *args, **kwargs) -> SelectType | int:
        session = PromptSession(self.console, self, state={"selected_index": 0})
        return session.run(live=True, transient=self.transient)


class MultiSelect(PromptBase, Generic[SelectType]):
    helper_text = "Use arrow keys (↑/↓) or k/j to move, press Space to toggle and Enter to submit"
    prompt_pointer = "\u276f "
    prompt_toggled_on = "\u2611 "
    prompt_toggled_off = "\u2610 "

    def __init__(
        self,
        choices: list[SelectType],
        prompt: TextType = "",
        return_indexes: bool = False,
        *,
        console: Console | None = None,
        indent: int = 2,
        transient: bool = False,
        prompt_suffix: str = ":",
    ):
        self.choices = choices
        self.return_indexes = return_indexes
        self.indent = indent
        self.transient = transient
        self.prompt_suffix = prompt_suffix
        super().__init__(prompt, console=console)

    def render_choices(self, current_index: int, selected_indexes: set[int], final: bool = False) -> TextType:
        if self.prompt.plain:
            # choices_text = (
            #     self.prompt.copy()
            #     .append(self.prompt_suffix)
            #     .append("\n")
            #     .append(self.helper_text, style="ctfa.prompt.message")
            #     .append_text(NEWLINE_RESET)
            # )
            choices_text = (
                Text(self.helper_text, style="ctfa.prompt.message")
                .append("\n")
                .append_text(self.prompt.copy())
                .append(self.prompt_suffix)
                .append_text(NEWLINE_RESET)
            )
        else:
            choices_text = Text(self.helper_text, style="ctfa.prompt.message").append_text(NEWLINE_RESET)

        indent_str = " " * self.indent

        for i, choice in enumerate(self.choices):
            if i == current_index and not final:
                choices_text.append(f"{indent_str}{self.prompt_pointer}", style="ctfa.prompt.pointer")
            else:
                choices_text.append(f"{indent_str}  ")

            if i in selected_indexes:
                choices_text.append(self.prompt_toggled_on, style="ctfa.prompt.toggled_on")
                choices_text.append(f"{choice}", style="ctfa.prompt.selected")
            else:
                choices_text.append(self.prompt_toggled_off, style="ctfa.prompt.toggled_off")
                choices_text.append(f"{choice}", style="ctfa.prompt.unselected")

            choices_text.append("\n")

        return choices_text

    def make_prompt(self, session: PromptSession) -> TextType:
        if "current_index" not in session.state:
            session.state["current_index"] = 0

        if "selected_indexes" not in session.state:
            session.state["selected_indexes"] = set()

        current_index = session.state["current_index"]
        selected_indexes = session.state["selected_indexes"]
        return self.render_choices(current_index, selected_indexes)

    def get_input(self, session: PromptSession, prompt: TextType | None = None) -> list[SelectType] | list[int]:
        # session.live will always be set if this method is called
        live = cast(Live, session.live)

        while True:
            current_index: int = session.state.get("current_index", 0)
            selected_indexes: set[int] = session.state.get("selected_indexes", set())

            key = readkey()

            if key == _key.UP or key == "k":
                current_index = max(0, current_index - 1)
            elif key == _key.DOWN or key == "j":
                current_index = min(len(self.choices) - 1, current_index + 1)
            elif key == _key.SPACE:
                if current_index in selected_indexes:
                    selected_indexes.remove(current_index)
                else:
                    selected_indexes.add(current_index)
            elif key == _key.ENTER:
                live.update(
                    self.render_choices(current_index, selected_indexes, final=True),
                    refresh=True,
                )
                live.stop()
                break

            live.update(self.render_choices(current_index, selected_indexes), refresh=True)

            session.state["current_index"] = current_index
            session.state["selected_indexes"] = selected_indexes

        return list(selected_indexes) if self.return_indexes else [self.choices[i] for i in selected_indexes]

    def process_response(
        self, session: PromptSession, response: list[SelectType] | list[int]
    ) -> list[SelectType] | list[int]:
        return response

    def execute(self, *args, **kwargs) -> list[SelectType] | list[int]:
        session = PromptSession(self.console, self, state={"current_index": 0, "selected_indexes": set()})
        return session.run(live=True, transient=self.transient)
