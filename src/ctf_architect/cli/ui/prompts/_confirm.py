from __future__ import annotations

from rich.console import Console
from rich.text import TextType

from ctf_architect.cli.ui.prompts._select import Select
from ctf_architect.cli.ui.prompts.session import PromptSession


class Confirm(Select[bool]):
    def __init__(
        self,
        prompt: TextType = "",
        yes_text: TextType = "Yes",
        no_text: TextType = "No",
        *,
        console: Console | None = None,
        indent: int = 2,
        transient: bool = False,
        prompt_suffix: str = "",
    ):
        self.yes_text = yes_text
        self.no_text = no_text
        super().__init__(
            [yes_text, no_text],  # type: ignore
            prompt,
            return_index=True,
            console=console,
            indent=indent,
            transient=transient,
            prompt_suffix=prompt_suffix,
        )

    def process_response(self, session: PromptSession, response: int) -> bool:
        if response == 0:
            return True
        return False
