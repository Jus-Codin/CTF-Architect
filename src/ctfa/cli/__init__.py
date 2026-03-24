from __future__ import annotations

from cyclopts import App

from ctfa.cli.ui.console import console
from ctfa.constants import APP_CMD_NAME
from ctfa.version import CTFA_VERSION

app = App(name=APP_CMD_NAME, console=console, version=CTFA_VERSION)

app.command("ctfa.cli.commands.chall:app", name="chall")
app.command("ctfa.cli.commands.repo:app", name="repo")
