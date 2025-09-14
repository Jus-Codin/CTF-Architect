from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, StrictUndefined

if TYPE_CHECKING:
    from ctf_architect.models import ChallengeConfig, CTFConfig, Service


def is_path_object(path: Path) -> bool:
    """Check if the given path is a Path object."""
    return isinstance(path, Path)


_env = None


def get_template_env() -> Environment:
    """Get the Jinja2 environment for rendering templates."""
    global _env
    if _env is None:
        _env = Environment(
            loader=PackageLoader("ctf_architect", "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        _env.tests["path_object"] = is_path_object
    return _env


def render_challenge_readme(challenge: ChallengeConfig) -> str:
    """Render the README for a challenge."""
    env = get_template_env()
    template = env.get_template("challenge.md.j2")
    return template.render(challenge=challenge)


def render_category_readme(
    category_name: str,
    ctf_config: CTFConfig,
    distribution: dict[str, int],
    challenges: list[ChallengeConfig],
    services: list[tuple[Service, ChallengeConfig]],
) -> str:
    """Render the README for a category."""
    env = get_template_env()
    template = env.get_template("category.md.j2")
    return template.render(
        category_name=category_name,
        ctf_config=ctf_config,
        distribution=distribution,
        challenges=challenges,
        services=services,
    )


def render_repo_readme(
    ctf_config: CTFConfig,
    distributions: dict[str, dict[str, int]],
    challenges: list[ChallengeConfig],
    services: list[tuple[Service, ChallengeConfig]],
) -> str:
    """Render the root README for the repository."""
    env = get_template_env()
    template = env.get_template("repo.md.j2")
    return template.render(
        ctf_config=ctf_config,
        distributions=distributions,
        challenges=challenges,
        services=services,
    )
