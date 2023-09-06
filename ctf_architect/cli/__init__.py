from __future__ import annotations

import typer

from ctf_architect.cli.challenge import challenge_app
from ctf_architect.cli.stats import stats_app


app = typer.Typer()
app.add_typer(challenge_app, name="challenge")
app.add_typer(stats_app, name="stats")