from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from ctf_architect.core.challenge import Challenge
from ctf_architect.core.repo import Repo
from ctf_architect.models.base import SlugStr

if TYPE_CHECKING:
    from ctf_architect.core.action import DeploymentAction, DeploymentActionResult

T = TypeVar("T", bound="StrategyConfig")


class StrategyConfig(BaseModel):
    pass


class DeploymentStrategy(ABC, Generic[T]):
    """Base class for deployment strategies.

    Deployment strategies are responsible for either generating configuration files or directly deploying
    challenges to a target platform.

    Generation Lifecycle:
        1. Plan -> Preview actions (no side effects).
        2. Check Conflicts -> Detect conflicts (file overwrites, API duplicates, etc.). (Done outside of this class)
        3. Generate -> Actually perform the deployment (write files, call APIs, etc.). (Done outside of this class)
        4. Rollback -> Rollback the deployment if needed.

    Attributes:
        config (StrategyConfig): The configuration for the deployment strategy.
        output_dir (Path): The output directory for the deployment artifacts.
        dependencies (list[str]): A list of names of other deployments that this strategy depends on.
    """

    strategy_name: ClassVar[SlugStr]
    config_model: ClassVar[type[StrategyConfig]]
    can_rollback: ClassVar[bool]

    def __init__(self, config: T, output_dir: Path, dependencies: list[str] | None = None) -> None:
        self.config = config
        self.output_dir = output_dir
        self.dependencies = dependencies or []  # ensure it's a list

    @abstractmethod
    def plan(
        self, repo: Repo, challenges: Iterable[Challenge], dependencies_actions: dict[str, list[DeploymentAction]]
    ) -> list[DeploymentAction]:
        """Plan the deployment actions based on the configuration and dependencies actions.

        Args:
            repo (Repo): The repository containing the challenges and configurations.
            challenges (Iterable[Challenge]): An iterable of Challenge objects to be deployed.
            dependencies_actions (dict[str, list[DeploymentAction]]): A dictionary mapping deployment names to their respective actions.

        Returns:
            list[DeploymentAction]: A list of planned deployment actions.
        """
        pass

    def rollback(
        self, results: list[DeploymentActionResult], dependencies_results: dict[str, list[DeploymentActionResult]]
    ) -> None:
        """Rollback the deployment based on the results of the generate method.

        Args:
            results (list[DeploymentActionResult]): The results of the deployment strategy execution to be rolled back.
            dependencies_results (dict[str, list[DeploymentActionResult]]): A dictionary mapping deployment strategy names to their respective action results.
        """
        pass
