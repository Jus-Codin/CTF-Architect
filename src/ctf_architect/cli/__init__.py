from __future__ import annotations

from cyclopts import App

from ctf_architect.cli.commands.chall import app as chall_app
from ctf_architect.cli.commands.repo import app as repo_app
from ctf_architect.cli.ui.console import console
from ctf_architect.constants import APP_CMD_NAME

app = App(name=APP_CMD_NAME, group="CTF Architect", console=console)

app.command(chall_app)
app.command(repo_app)


def main():
    try:
        app()
    except KeyboardInterrupt:
        console.print("Aborted by user", style="ctfa.error")
