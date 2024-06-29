from __future__ import annotations

import typer

from ctf_architect.chall_architect.terminal.main import main as terminal_main

app = typer.Typer()


@app.command()
def callback():
    """
    Creates a challenge folder in the current directory
    """
    terminal_main()
