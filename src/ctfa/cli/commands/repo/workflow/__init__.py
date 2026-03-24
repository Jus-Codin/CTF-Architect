from __future__ import annotations

from cyclopts import App

app = App(
    name="workflow",
    group="Repository Workflow Commands",
    help="Commands for planning and executing repository workflows",
)

app.command("ctfa.cli.commands.repo.workflow.plan:command", name="plan")
app.command("ctfa.cli.commands.repo.workflow.apply:command", name="apply")
