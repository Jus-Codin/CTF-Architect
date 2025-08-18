import importlib.metadata

from ctf_architect.core.challenge import Challenge
from ctf_architect.core.compose import create_compose_files, update_compose_files
from ctf_architect.core.initialize import init_chall
from ctf_architect.core.lint import lint_challenge, lint_challenge_repo
from ctf_architect.core.port_mapping import generate_port_mapping, load_port_mapping, save_port_mapping
from ctf_architect.core.repo import Repo
from ctf_architect.core.rules import add_rule, get_rule, rule
from ctf_architect.utils import is_challenge_folder, is_challenge_repo

__all__ = [
    "is_challenge_folder",
    "create_compose_files",
    "update_compose_files",
    "init_chall",
    "lint_challenge",
    "lint_challenge_repo",
    "load_port_mapping",
    "save_port_mapping",
    "generate_port_mapping",
    "is_challenge_repo",
    "get_rule",
    "add_rule",
    "rule",
    "Challenge",
    "Repo",
]

__version__ = importlib.metadata.version("ctf-architect")
