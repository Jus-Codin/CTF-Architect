from __future__ import annotations

from cyclopts import App

app = App(
    name="config",
    group="Repository Configuration Commands",
    help="Commands for managing CTF challenge repository configuration",
)

app.command("ctfa.cli.commands.repo.config.show:command", name="show")
