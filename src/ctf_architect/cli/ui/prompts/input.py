from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from rich.console import Console
from rich.text import Text, TextType

from ctf_architect.cli.ui.prompts.base import PromptBase
from ctf_architect.cli.ui.prompts.session import InvalidResponse, PromptSession

InputType = TypeVar("InputType")

NEWLINE_RESET = Text("\n", style="reset")


class InputPromptBase(PromptBase, Generic[InputType]):
    response_type: type = str
    validate_error_message = "[ctfa.prompt.error]Please enter a valid value"

    def __init__(
        self,
        prompt: TextType = "",
        *,
        console: Console | None = None,
        default: Any = ...,
        password: bool = False,
        show_default: bool = True,
        validator: Callable[[InputType], None] | None = None,
        prompt_suffix: str = ": ",
    ):
        self.default = default
        self.password = password
        self.show_default = show_default
        self.validator = validator
        self.prompt_suffix = prompt_suffix
        super().__init__(prompt, console=console)

    def render_default(self, default: Any) -> TextType:
        return Text(f"({default})", style="ctfa.prompt.default")

    def make_prompt(self, session: PromptSession) -> TextType:
        prompt = self.prompt.copy()
        prompt.end = ""

        if self.default != ... and self.show_default and isinstance(self.default, (str, self.response_type)):  # noqa: UP038
            prompt.append(" ")
            _default = self.render_default(self.default)
            prompt.append(_default)

        prompt.append(self.prompt_suffix)
        return prompt

    def get_input(self, session: PromptSession, prompt: TextType | None = None) -> Any:
        return session.console.input(prompt, password=self.password)  # type: ignore

    def process_response(self, session: PromptSession, response: str) -> InputType:
        if response == "" and self.default != ...:
            return self.default

        response = response.strip()

        try:
            processed = self.response_type(response)
        except ValueError:
            raise InvalidResponse(self.validate_error_message)

        if self.validator is not None:
            self.validator(processed)

        return processed

    def execute(self, *args, **kwargs) -> InputType:
        session = PromptSession(self.console, self)
        return session.run()


class InputStr(InputPromptBase[str]):
    response_type = str

    def __init__(
        self,
        prompt: TextType = "",
        *,
        console: Console | None = None,
        allow_empty: bool = True,
        default: Any = ...,
        password: bool = False,
        show_default: bool = True,
        validator: Callable[[str], None] | None = None,
        prompt_suffix: str = ": ",
    ):
        self.allow_empty = allow_empty

        super().__init__(
            prompt,
            console=console,
            default=default,
            password=password,
            show_default=show_default,
            validator=validator,
            prompt_suffix=prompt_suffix,
        )

    def process_response(self, session: PromptSession, response: str) -> str:
        if response == "" and self.default == ... and not self.allow_empty:
            raise InvalidResponse("[ctfa.prompt.error]Please enter a value")

        return super().process_response(session, response)


class InputInt(InputPromptBase[int]):
    response_type = int
    validate_error_message = "[ctfa.prompt.error]Please enter a valid integer"


class InputFloat(InputPromptBase[float]):
    response_type = float
    validate_error_message = "[ctfa.prompt.error]Please enter a number"


class MultilineInput(PromptBase):
    helper_text = "Press Ctrl-D (or Ctrl-Z on Windows) to finish input."

    def __init__(
        self,
        prompt: TextType = "",
        *,
        allow_empty: bool = True,
        console: Console | None = None,
        validator: Callable[[str], None] | None = None,
        prompt_suffix: str = ":",
    ):
        self.allow_empty = allow_empty
        self.validator = validator
        self.prompt_suffix = prompt_suffix
        super().__init__(prompt, console=console)

    def make_prompt(self, session: PromptSession) -> TextType:
        if self.prompt.plain:
            # prompt = (
            #     self.prompt.copy()
            #     .append(self.prompt_suffix)
            #     .append("\n")
            #     .append(self.helper_text, style="ctfa.prompt.message")
            #     .append_text(NEWLINE_RESET)
            # )
            prompt = (
                Text(self.helper_text, style="ctfa.prompt.message")
                .append("\n")
                .append_text(self.prompt.copy())
                .append(self.prompt_suffix)
                .append_text(NEWLINE_RESET)
            )
        else:
            prompt = Text(self.helper_text, style="ctfa.prompt.message").append_text(NEWLINE_RESET)

        prompt.end = ""

        return prompt

    def get_input(self, session: PromptSession, prompt: TextType | None = None) -> Any:
        session.console.print(prompt)
        return sys.stdin.read()

    def process_response(self, session: PromptSession, response: str) -> str:
        if response == "" and not self.allow_empty:
            raise InvalidResponse("[ctfa.prompt.error]Please enter a value")

        if self.validator is not None:
            self.validator(response)
        return response

    def execute(self, *args, **kwargs) -> str:
        session = PromptSession(self.console, self)
        return session.run()
