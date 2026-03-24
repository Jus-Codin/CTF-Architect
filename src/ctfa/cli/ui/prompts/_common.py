from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from readchar import readkey
from rich.console import Console, RenderableType
from rich.live import Live
from rich.text import Text, TextType

from ..console import console as _console


class _MISSING:
    pass


MISSING: Any = _MISSING()


class PromptError(Exception):
    pass


class InvalidResponse(PromptError):
    def __init__(self, message: TextType):
        self.message = message

    def __rich__(self) -> TextType:
        return self.message


class PromptCancelled(PromptError):
    """Raised when a prompt session is cancelled by the user."""

    pass


class PromptStatus(Enum):
    INITIALIZING = auto()
    RUNNING = auto()
    DONE = auto()
    CANCELLED = auto()


class PromptBase(ABC):
    def __init__(
        self,
        question: TextType = "",
        *,
        console: Console | None = None,
        state_key: str | None = None,
    ):
        self.question = (
            Text.from_markup(question, style="ctfa.prompt.message") if isinstance(question, str) else question
        )
        self.console = console or _console
        self.state_key = state_key or uuid4()

    def state(self, session: PromptSession) -> dict[str, Any]:
        """Get the current state dictionary for the prompt session.

        Args:
            session (PromptSession): The current prompt session.

        Returns:
            dict[str, Any]: The state dictionary.
        """
        return session.state.setdefault(f"{self.__class__.__name__}:{self.state_key}", {})

    @abstractmethod
    def render(self, session: PromptSession, processed: Any = MISSING) -> RenderableType:
        """Called in the session loop to render the prompt.

        If the session is live, this will be called to update the prompt in the loop.

        Args:
            session (PromptSession): The current prompt session.
            processed (Any): The processed response, if any.

        Returns:
            RenderableType: The rendered prompt.
        """

    def get_input(self, session: PromptSession, prompt: RenderableType | None = None) -> str:
        """Called in the session loop to get user input.

        Args:
            session (PromptSession): The current prompt session.
            prompt (RenderableType | None): The prompt to display for input.

        Returns:
            str: The user input.
        """
        if session.live is None:
            return session.console.input(prompt)  # type: ignore
        else:
            return readkey()

    @abstractmethod
    def handle_input(self, session: PromptSession, response: Any) -> Any:
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

    @abstractmethod
    def ask(self, *args, **kwargs) -> Any:
        """Start a prompt session and return the result."""


class PromptSession:
    def __init__(
        self,
        console: Console,
        prompt: PromptBase,
        state: dict[str, Any] | None = None,
    ):
        self.console = console
        self.prompt = prompt
        self.state = state or {}

        self.status = PromptStatus.INITIALIZING
        self.live = None

    def _run_static(self, password: bool = False):
        while True:
            prompt = self.prompt.render(self)
            response = self.prompt.get_input(self, prompt)

            try:
                processed = self.prompt.handle_input(self, response)
            except InvalidResponse as e:
                self.prompt.on_validation_error(self, response, e)
                continue

            # Only exit when the prompt explicitly indicates it is done
            if self.status == PromptStatus.DONE:
                return processed

    def _run_live(self, transient: bool = False):
        with Live(
            self.prompt.render(self),
            console=self.console,
            auto_refresh=False,
            transient=transient,
        ) as live:
            self.live = live

            while True:
                prompt = self.prompt.render(self)
                live.update(prompt, refresh=True)

                response = self.prompt.get_input(self, prompt)

                try:
                    processed = self.prompt.handle_input(self, response)
                except InvalidResponse as e:
                    self.prompt.on_validation_error(self, response, e)
                    continue

                if self.status == PromptStatus.DONE:
                    # Do a final update to show the completed prompt state
                    live.update(self.prompt.render(self, processed), refresh=True)
                    live.stop()
                    return processed

    def run(self, live: bool = False, *, transient: bool = False, password: bool = False):
        if self.status != PromptStatus.INITIALIZING:
            raise PromptError("Prompt session is already running or has completed.")

        self.status = PromptStatus.RUNNING

        try:
            if live:
                return self._run_live(transient=transient)
            else:
                return self._run_static(password=password)
        except KeyboardInterrupt:
            self.status = PromptStatus.CANCELLED
            raise PromptCancelled("Cancelled by the user.")
