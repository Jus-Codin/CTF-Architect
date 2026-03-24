from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from readchar import key as _key
from rich.console import Console
from rich.text import Text, TextType

from ..core import MISSING, PromptComponent, PromptSession, PromptStatus

T = TypeVar("T")

NEWLINE_RESET = Text("\n", style="reset")


class Select(PromptComponent, Generic[T]):
    instruction_text = "Use arrow keys (↑/↓) or k/j to move and press Enter to select"
    prompt_pointer = "\u276f "

    def __init__(
        self,
        question: TextType,
        choices: Sequence[T],
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
        super().__init__(question, console=console)

    def _render_choices(self, selected_index: int) -> TextType:
        if self.question.plain:
            choices_text = (
                self.question.copy()
                .append(self.prompt_suffix)
                .append(f"\n{self.instruction_text}", style="ctfa.prompt.message")
            )
        else:
            choices_text = Text(self.instruction_text, style="ctfa.prompt.message")

        choices_text.append_text(NEWLINE_RESET)

        indent_str = " " * self.indent

        for i, choice in enumerate(self.choices):
            if i == selected_index:
                choices_text.append(f"{indent_str}{self.prompt_pointer}", style="ctfa.prompt.pointer")
                choices_text.append(f"{choice}\n", style="ctfa.prompt.selected")
            else:
                choices_text.append(f"{indent_str}  {choice}\n", style="ctfa.prompt.choices")

        return choices_text

    def _render_result(self, selected_index: int) -> TextType:
        if self.question.plain:
            result_text = self.question.copy()
        else:
            result_text = Text("Answer", style="ctfa.prompt.message")
        result_text.append(self.prompt_suffix)
        result_text.append(f" {self.choices[selected_index]}", style="ctfa.prompt.answer")
        return result_text

    def render(self, session: PromptSession, processed: T = MISSING) -> TextType:
        selected_index = session.state.get("selected_index", 0)

        if processed is not MISSING:
            return self._render_result(selected_index)

        return self._render_choices(selected_index)

    def process_input(self, session: PromptSession, response: str) -> T | int:
        selected_index = session.state.get("selected_index", 0)

        if response in (_key.UP, "k"):
            selected_index = (selected_index - 1) % len(self.choices)
        elif response in (_key.DOWN, "j"):
            selected_index = (selected_index + 1) % len(self.choices)
        elif response == _key.ENTER:
            session.status = PromptStatus.DONE
            if self.return_index:
                return selected_index
            else:
                return self.choices[selected_index]

        session.state["selected_index"] = selected_index
        return MISSING

    def ask(self, *args, **kwargs) -> T | int:
        session = PromptSession(self.console, self)
        return session.run(live=True, transient=self.transient)


class MultiSelect(PromptComponent, Generic[T]):
    instruction_text = "Use arrow keys (↑/↓) or k/j to move, space to select, and Enter to confirm"
    prompt_pointer = "\u276f "
    prompt_toggled_on = "\u2611 "
    prompt_toggled_off = "\u2610 "

    def __init__(
        self,
        question: TextType,
        choices: Sequence[T],
        return_indices: bool = False,
        *,
        console: Console | None = None,
        indent: int = 2,
        transient: bool = False,
        prompt_suffix: str = ":",
    ):
        self.choices = choices
        self.return_indices = return_indices
        self.indent = indent
        self.transient = transient
        self.prompt_suffix = prompt_suffix
        super().__init__(question, console=console)

    def _render_choices(self, selected_index: int, toggled_indices: set[int]) -> TextType:
        if self.question.plain:
            choices_text = (
                self.question.copy()
                .append(self.prompt_suffix)
                .append(f"\n{self.instruction_text}", style="ctfa.prompt.message")
            )
        else:
            choices_text = Text(self.instruction_text, style="ctfa.prompt.message")

        choices_text.append_text(NEWLINE_RESET)

        indent_str = " " * self.indent

        for i, choice in enumerate(self.choices):
            pointer = f"{indent_str}{self.prompt_pointer}" if i == selected_index else f"{indent_str}  "
            toggle = self.prompt_toggled_on if i in toggled_indices else self.prompt_toggled_off
            style = "ctfa.prompt.selected" if i == selected_index else "ctfa.prompt.choices"
            choices_text.append(f"{pointer}{toggle} {choice}\n", style=style)

        return choices_text

    def render(self, session: PromptSession, processed: list[T] = MISSING) -> TextType:
        selected_index = session.state.get("selected_index", 0)
        toggled_indices = session.state.get("toggled_indices", set())
        return self._render_choices(selected_index, toggled_indices)

    def process_input(self, session: PromptSession, response: str) -> list[T] | list[int] | None:
        selected_index = session.state.get("selected_index", 0)
        toggled_indices = session.state.get("toggled_indices", set())

        if response in (_key.UP, "k"):
            selected_index = (selected_index - 1) % len(self.choices)
        elif response in (_key.DOWN, "j"):
            selected_index = (selected_index + 1) % len(self.choices)
        elif response == _key.SPACE:
            if selected_index in toggled_indices:
                toggled_indices.remove(selected_index)
            else:
                toggled_indices.add(selected_index)
        elif response == _key.ENTER:
            session.status = PromptStatus.DONE
            if self.return_indices:
                return list(toggled_indices)
            else:
                return [self.choices[i] for i in toggled_indices]

        session.state["selected_index"] = selected_index
        session.state["toggled_indices"] = toggled_indices
        return MISSING

    def ask(self, *args, **kwargs) -> list[T] | list[int]:
        session = PromptSession(self.console, self)
        return session.run(live=True, transient=self.transient)
