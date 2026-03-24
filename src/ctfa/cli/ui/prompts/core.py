from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any

from readchar import readkey
from rich.console import Console, RenderableType
from rich.live import Live
from rich.text import Text, TextType

from ..console import console as _console


class _MISSING:
    pass


MISSING: Any = _MISSING()


class PromptError(Exception):
    """Base class for all prompt exceptions."""


class PromptCancelled(PromptError):
    """Raised when a prompt or flow is cancelled by the user."""


class PromptValidationError(PromptError):
    """Raised when user input fails validation and should be retried."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class PromptStatus(Enum):
    INITIALIZING = auto()
    RUNNING = auto()
    DONE = auto()
    CANCELLED = auto()


class PromptComponent(ABC):
    """Interface for stateless prompt components.

    Components should not mutate ``self`` during execution. They receive all
    mutable state through ``PromptContext`` and the session.
    """

    prompt_type: str

    def __init__(
        self,
        question: TextType = "",
        *,
        console: Console | None = None,
    ):
        self.question = (
            Text.from_markup(question, style="ctfa.prompt.message") if isinstance(question, str) else question
        )
        self.console = console or _console

    @abstractmethod
    def render(self, session: PromptSession, processed: Any = MISSING) -> RenderableType:
        """Render the prompt for display.

        Args:
            session (PromptSession): The current prompt session.
            processed (Any, optional): Previously processed input, if any.

        Returns:
            RenderableType: The rendered prompt.
        """

    def get_input(self, session: PromptSession, prompt: RenderableType | None = None) -> str:
        """Get user input for the prompt.

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
    def process_input(self, session: PromptSession, response: str) -> Any:
        """Process raw user input into a final value.

        Args:
            session (PromptSession): The current prompt session.
            response (str): The raw user input.

        Returns:
            Any: The processed input value.
        """

    def on_validation_error(self, session: PromptSession, error: PromptValidationError) -> None:
        """Hook called when input validation fails.

        Args:
            session (PromptSession): The current prompt session.
            error (PromptValidationError): The validation error raised.
        """
        session.console.print(error, style="ctfa.prompt.error")

    @abstractmethod
    def ask(self, *args, **kwargs) -> Any:
        """Start a prompt session for this component, and return the result.

        Returns:
            Any: The processed input value.
        """


class PromptSession:
    """Holds all mutable state for a single run of a prompt.

    The session handles console interaction, catches validation errors,
    and provides a stable place to store state of a running prompt.
    """

    def __init__(
        self,
        console: Console,
        component: PromptComponent,
        state: dict[str, Any] | None = None,
    ):
        self.console = console
        self.component = component
        self.state = state or {}

        self.status = PromptStatus.INITIALIZING
        self.live = None

    def _run_static(self, *, metadata: dict[str, Any] | None = None):
        while True:
            prompt = self.component.render(self)
            response = self.component.get_input(self, prompt)

            try:
                processed = self.component.process_input(self, response)
            except PromptValidationError as e:
                self.component.on_validation_error(self, e)
                continue

            # Only exit when prompt explicitly indicates it is done
            if self.status == PromptStatus.DONE:
                return processed

    def _run_live(self, *, transient: bool = False, metadata: dict[str, Any] | None = None):
        with Live(
            self.component.render(self),
            console=self.console,
            auto_refresh=False,
            transient=transient,
        ) as live:
            self.live = live

            while True:
                prompt = self.component.render(self)
                live.update(prompt, refresh=True)

                response = self.component.get_input(self, prompt)

                try:
                    processed = self.component.process_input(self, response)
                except PromptValidationError as e:
                    self.component.on_validation_error(self, e)
                    continue

                # Only exit when prompt explicitly indicates it is done
                if self.status == PromptStatus.DONE:
                    # Do a final update to show the completed prompt state
                    live.update(self.component.render(self, processed), refresh=True)
                    live.stop()
                    return processed

    def run(
        self,
        live: bool = False,
        *,
        transient: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        if self.status != PromptStatus.INITIALIZING:
            raise PromptError("Prompt session is already running or has completed.")

        self.status = PromptStatus.RUNNING

        try:
            if live:
                return self._run_live(transient=transient, metadata=metadata)
            else:
                return self._run_static(metadata=metadata)
        except KeyboardInterrupt:
            self.status = PromptStatus.CANCELLED
            raise PromptCancelled("Prompt cancelled by user.")
