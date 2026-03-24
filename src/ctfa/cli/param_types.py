from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any

from cyclopts import Parameter
from cyclopts.types import _path_resolve_converter

from ctfa.utils import is_challenge_folder, is_challenge_repo


def _validate_challenge_folder(type_: Any, path: Any):
    if isinstance(path, Sequence):
        if isinstance(path, str):
            raise TypeError

        for p in path:
            _validate_challenge_folder(type_, p)
    else:
        if not isinstance(path, Path):
            return

        if not is_challenge_folder(path):
            raise ValueError(f"The path '{path}' is not a valid challenge folder.")


def _validate_non_challenge_folder(type_: Any, path: Any):
    if isinstance(path, Sequence):
        if isinstance(path, str):
            raise TypeError

        for p in path:
            _validate_non_challenge_folder(type_, p)
    else:
        if not isinstance(path, Path):
            return

        if is_challenge_folder(path):
            raise ValueError(f"The path '{path}' is already a challenge folder.")


def _validate_challenge_repo(type_: Any, path: Any):
    if isinstance(path, Sequence):
        if isinstance(path, str):
            raise TypeError

        for p in path:
            _validate_challenge_repo(type_, p)
    else:
        if not isinstance(path, Path):
            return

        if not is_challenge_repo(path):
            raise ValueError(f"The path '{path}' is not a valid challenge repository.")


ExistingChallengeFolder = Annotated[Path, Parameter(validator=_validate_challenge_folder)]
ResolvedExistingChallengeFolder = Annotated[ExistingChallengeFolder, Parameter(converter=_path_resolve_converter)]
NonChallengeFolder = Annotated[Path, Parameter(validator=_validate_non_challenge_folder)]
ResolvedNonChallengeFolder = Annotated[NonChallengeFolder, Parameter(converter=_path_resolve_converter)]
ExistingChallengeRepository = Annotated[Path, Parameter(validator=_validate_challenge_repo)]
ResolvedExistingChallengeRepository = Annotated[
    ExistingChallengeRepository, Parameter(converter=_path_resolve_converter)
]
