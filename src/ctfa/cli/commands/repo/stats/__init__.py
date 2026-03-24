from __future__ import annotations

from cyclopts import App

app = App(
    name="stats",
    group="Repository Statistics Commands",
    help="Commands for generating statistics about CTF challenge repositories",
)

app.command("ctfa.cli.commands.repo.stats.update:command", name="update")
