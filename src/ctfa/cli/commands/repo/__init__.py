from __future__ import annotations

from cyclopts import App

app = App(
    name="repo",
    group="Repository Commands",
    help="Commands for managing CTF challenge repositories",
)

app.command("ctfa.cli.commands.repo.config.__init__:app", name="config")
app.command("ctfa.cli.commands.repo._import:command", name="import")
app.command("ctfa.cli.commands.repo.init:command", name="init")
app.command("ctfa.cli.commands.repo.lint:command", name="lint")
app.command("ctfa.cli.commands.repo.stats.__init__:app", name="stats")
app.command("ctfa.cli.commands.repo.workflow.__init__:app", name="workflow")
