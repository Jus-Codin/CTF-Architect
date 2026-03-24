from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from rich.console import Console, RenderableType
from rich.text import Text, TextType

from ..core import (
    MISSING,
    PromptComponent,
    PromptSession,
    PromptStatus,
    PromptValidationError,
)

T = TypeVar("T")

NEWLINE_RESET = Text("\n", style="reset")


class InputPromptBase(PromptComponent, Generic[T]):
    response_type: type = str
    validate_error_msg = "Please enter a valid value"

    def __init__(
        self,
        question: TextType = "",
        *,
        console: Console | None = None,
        default: Any = MISSING,
        password: bool = False,
        show_default: bool = True,
        validator: Callable[[T], bool | str] | None = None,
        prompt_suffix: str = ": ",
    ):
        self.default = default
        self.password = password
        self.show_default = show_default
        self.validator = validator
        self.prompt_suffix = prompt_suffix
        super().__init__(question, console=console)

    def _render_default(self, default: Any) -> TextType:
        return Text(f"({default})", style="ctfa.prompt.default")

    def render(self, session: PromptSession, processed: T = MISSING) -> TextType:
        prompt = self.question.copy()
        prompt.end = ""

        if self.default is not MISSING and self.show_default and isinstance(self.default, (str, self.response_type)):
            prompt.append(" ")
            _default = self._render_default(self.default)
            prompt.append(_default)

        prompt.append(self.prompt_suffix)
        return prompt

    def process_input(self, session: PromptSession, response: str) -> T:
        if response == "" and self.default is not MISSING:
            return self.default

        response = response.strip()

        try:
            processed = self.response_type(response)
        except ValueError:
            raise PromptValidationError(self.validate_error_msg)

        if self.validator is not None:
            result = self.validator(processed)
            if result is not True:
                raise PromptValidationError(result or self.validate_error_msg)

        session.status = PromptStatus.DONE
        return processed

    def ask(self, *args, **kwargs) -> T:
        session = PromptSession(self.console, self)
        return session.run()


class InputStr(InputPromptBase[str]):
    response_type: type = str

    def __init__(
        self,
        question: TextType = "",
        *,
        console: Console | None = None,
        allow_empty: bool = False,
        default: Any = MISSING,
        password: bool = False,
        show_default: bool = True,
        validator: Callable[[str], bool | str] | None = None,
        prompt_suffix: str = ": ",
    ):
        self.allow_empty = allow_empty

        super().__init__(
            question,
            console=console,
            default=default,
            password=password,
            show_default=show_default,
            validator=validator,
            prompt_suffix=prompt_suffix,
        )

    def process_input(self, session: PromptSession, response: str) -> str:
        if response == "" and self.default is not None and not self.allow_empty:
            raise PromptValidationError("Please enter a value")

        return super().process_input(session, response)


class InputInt(InputPromptBase[int]):
    response_type: type = int
    validate_error_msg = "Please enter a valid integer"


class InputFloat(InputPromptBase[float]):
    response_type: type = float
    validate_error_msg = "Please enter a valid number"


class MultilineInput(PromptComponent):
    instruction_text = "Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) then Enter to submit"

    def __init__(
        self,
        question: TextType = "",
        *,
        allow_empty: bool = False,
        console: Console | None = None,
        validator: Callable[[str], None] | None = None,
        prompt_suffix: str = ": ",
    ):
        self.allow_empty = allow_empty
        self.validator = validator
        self.prompt_suffix = prompt_suffix
        super().__init__(question, console=console)

    def render(self, session: PromptSession, processed: Any = MISSING) -> TextType:
        if self.question.plain:
            prompt = (
                self.question.copy()
                .append(self.prompt_suffix)
                .append(f"\n{self.instruction_text}", style="ctfa.prompt.message")
            )
        else:
            prompt = Text(self.instruction_text, style="ctfa.prompt.message")

        prompt.append("\n>")
        prompt.append(" ", style="reset")
        prompt.end = ""

        return prompt

    def get_input(self, session: PromptSession, prompt: RenderableType | None = None) -> str:
        session.console.print(prompt, end="")
        return sys.stdin.read()

    def process_input(self, session: PromptSession, response: str) -> str:
        if response == "" and not self.allow_empty:
            raise PromptValidationError("[ctfa.prompt.error]Please enter a value")

        if self.validator is not None:
            self.validator(response)

        session.status = PromptStatus.DONE
        return response

    def ask(self, *args, **kwargs) -> str:
        session = PromptSession(self.console, self)
        return session.run()
