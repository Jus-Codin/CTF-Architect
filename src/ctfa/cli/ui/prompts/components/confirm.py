from __future__ import annotations

from rich.console import Console
from rich.text import TextType

from ..core import PromptSession
from .select import Select


class Confirm(Select[bool]):
    def __init__(
        self,
        question: TextType = "",
        yes_text: TextType = "Yes",
        no_text: TextType = "No",
        *,
        console: Console | None = None,
        indent: int = 2,
        transient: bool = False,
        prompt_suffix: str = "?",
    ):
        self.yes_text = yes_text
        self.no_text = no_text
        super().__init__(
            question,
            [yes_text, no_text],  # type: ignore
            return_index=True,
            console=console,
            indent=indent,
            transient=transient,
            prompt_suffix=prompt_suffix,
        )

    def process_input(self, session: PromptSession, response: str) -> bool:
        result = super().process_input(session, response)
        if isinstance(result, int):
            return result == 0
        return result
