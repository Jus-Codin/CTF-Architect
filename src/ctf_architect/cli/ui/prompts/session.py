from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.live import Live
from rich.text import TextType

if TYPE_CHECKING:
    from ctf_architect.cli.ui.prompts.base import PromptBase


class InvalidResponse(Exception):
    def __init__(self, message: TextType):
        self.message = message

    def __rich__(self) -> TextType:
        return self.message


class PromptSession:
    def __init__(
        self,
        console: Console,
        prompt: PromptBase,
        state: dict[str, Any] = {},
    ):
        self.console = console
        self.current_prompt = prompt
        self.state = state

        self.running = False
        self.live = None

    def _run_static(self):
        while True:
            prompt = self.current_prompt.make_prompt(self)
            response = self.current_prompt.get_input(self, prompt)

            try:
                processed = self.current_prompt.process_response(self, response)
            except InvalidResponse as e:
                self.current_prompt.on_validation_error(self, response, e)
                continue

            return processed

    def _run_live(self, transient: bool = False):
        with Live(
            self.current_prompt.make_prompt(self),
            console=self.console,
            auto_refresh=False,
            transient=transient,
        ) as live:
            self.live = live

            while True:
                # This function should update the live prompt as well.
                response = self.current_prompt.get_input(self)

                try:
                    processed = self.current_prompt.process_response(self, response)
                except InvalidResponse as e:
                    self.current_prompt.on_validation_error(self, response, e)
                    continue

                return processed

    def run(self, live: bool = False, transient: bool = False):
        if self.running:
            raise RuntimeError("Prompt session is already running.")

        self.running = True

        if live:
            return self._run_live(transient)
        else:
            return self._run_static()
