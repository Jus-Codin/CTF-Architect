import importlib.metadata

from ctf_architect.core.challenge import is_challenge_folder, load_chall_config, save_chall_config, save_chall_readme
from ctf_architect.core.compose import create_compose_files, update_compose_files
from ctf_architect.core.initialize import init_chall, init_repo_from_config, init_repo_no_config
from ctf_architect.core.lint import lint_challenge, lint_challenge_repo
from ctf_architect.core.port_mapping import generate_port_mapping, load_port_mapping, save_port_mapping
from ctf_architect.core.repo import (
    add_challenge,
    find_challenge,
    find_challenge_folder,
    is_challenge_repo,
    load_repo_config,
    remove_challenge,
    save_repo_config,
    walk_challenge_folders,
    walk_challenges,
)
from ctf_architect.core.rules import add_rule, get_rule, rule
from ctf_architect.core.stats import update_category_readme, update_root_readme

__all__ = [
    "is_challenge_folder",
    "load_chall_config",
    "save_chall_config",
    "save_chall_readme",
    "create_compose_files",
    "update_compose_files",
    "init_chall",
    "init_repo_from_config",
    "init_repo_no_config",
    "lint_challenge",
    "lint_challenge_repo",
    "load_port_mapping",
    "save_port_mapping",
    "generate_port_mapping",
    "is_challenge_repo",
    "load_repo_config",
    "save_repo_config",
    "walk_challenge_folders",
    "find_challenge_folder",
    "find_challenge",
    "add_challenge",
    "remove_challenge",
    "walk_challenges",
    "get_rule",
    "add_rule",
    "rule",
    "update_category_readme",
    "update_root_readme",
]

__version__ = importlib.metadata.version("ctf-architect")
