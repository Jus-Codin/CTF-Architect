from __future__ import annotations

from cyclopts import App

app = App(
    name="chall",
    group="Challenge Commands",
    help="Commands for managing CTF challenges",
)

app.command("ctfa.cli.commands.chall.init:command", name="init")
app.command("ctfa.cli.commands.chall.lint:command", name="lint")
app.command("ctfa.cli.commands.chall.regen:command", name="regen", alias="regenerate")
app.command("ctfa.cli.commands.chall.flags:app", name="flag", alias="flags")
app.command("ctfa.cli.commands.chall.dist:app", name="dist")
