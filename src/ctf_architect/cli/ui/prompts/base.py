from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console
from rich.text import Text, TextType

from ctf_architect.cli.ui.console import console as _console
from ctf_architect.cli.ui.prompts.session import PromptSession


class PromptBase(ABC):
    def __init__(
        self,
        prompt: TextType = "",
        *,
        console: Console | None = None,
    ):
        self.prompt = Text.from_markup(prompt, style="ctfa.prompt.message") if isinstance(prompt, str) else prompt
        self.console = console or _console

    @abstractmethod
    def make_prompt(self, session: PromptSession) -> TextType:
        """Called in the session loop to render the prompt.

        If the session is live, this will be called to update the prompt in the loop.

        Args:
            session (PromptSession): The current prompt session.

        Returns:
            TextType: The rendered prompt.
        """

    @abstractmethod
    def get_input(self, session: PromptSession, prompt: TextType | None = None) -> Any:
        """Called in the session loop to get the user input.

        This is then passed to the `process_response` method to validate and process the response.

        Args:
            session (PromptSession): The current prompt session.
            prompt (TextType, optional): The prompt to display. Defaults to None.

        Returns:
            Any: The user input.
        """

    @abstractmethod
    def process_response(self, session: PromptSession, response: Any) -> Any:
        """Called in the session loop to process the user input.

        This method should validate the response and return the processed value.

        Args:
            session (PromptSession): The current prompt session.
            response (str): The user input.

        Returns:
            Any: The processed response.
        """

    def on_validation_error(self, session: PromptSession, response: str, error: Exception) -> None:
        """Called when a validation error occurs.

        Args:
            session (PromptSession): The current prompt session.
            response (str): The response that caused the error.
            error (Exception): The exception that was raised.
        """
        session.console.print(error, style="ctfa.prompt.error")

    def execute(self, *args, **kwargs) -> Any:
        """Start the prompt session loop."""
        session = PromptSession(self.console, self)
        return session.run()
