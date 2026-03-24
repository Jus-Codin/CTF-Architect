from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.tree import Tree

from ctfa.core.rules import SeverityLevel

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions, RenderResult

    from ctfa.core.lint import LintResult
    from ctfa.models.challenge import ChallengeConfig
    from ctfa.models.ctf_config import CTFConfig


class ChallengeConfigComponent:
    def __init__(self, config: ChallengeConfig):
        self.config = config

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Panel(
            f"  [ctfa.title]Name: {self.config.name}[/ctfa.title]\n"
            f"  [ctfa.info]ID:[/ctfa.info] {self.config.id}\n"
            f"  [ctfa.info]Description:[/ctfa.info] {self.config.description}\n"
            f"  [ctfa.info]Category:[/ctfa.info] {self.config.category.capitalize()}\n"
            f"  [ctfa.info]Difficulty:[/ctfa.info] {self.config.difficulty.capitalize()}\n"
            f"  [ctfa.info]Author:[/ctfa.info] {self.config.author}\n"
            f"  [ctfa.info]Folder Name:[/ctfa.info] {self.config.folder_name}",
            title="Challenge Configuration",
            title_align="left",
            border_style="green",
        )


class CTFConfigComponent:
    def __init__(self, config: CTFConfig):
        self.config = config

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Panel(
            f"  [ctfa.title]Name: {self.config.name}[/ctfa.title]\n"
            f"  [ctfa.info]Flag Format:[/ctfa.info] {self.config.flag_format or 'None'}\n"
            f"  [ctfa.info]Starting Port:[/ctfa.info] {self.config.starting_port or 'None'}",
            title="CTF Configuration",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
        yield Panel(
            "\n".join([f"  - {category.capitalize()}" for category in self.config.categories]),
            title="Categories",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
        yield Panel(
            "\n".join([f"  - {difficulty.capitalize()}" for difficulty in self.config.difficulties]),
            title="Difficulties",
            title_align="left",
            style="ctfa.info",
            border_style="green",
        )
        if self.config.extra_labels:
            yield Panel(
                "\n".join([f"  - {extra.name} ({extra.type})" for extra in self.config.extra_labels]),
                title="Extra Labels",
                title_align="left",
                style="ctfa.info",
                border_style="green",
            )


class ChallengeLintResultComponent:
    # SeverityLevel -> (style, icon)
    VIOLATION_STYLES = {
        SeverityLevel.FATAL: ("ctfa.lint.level.fatal", "✕"),
        SeverityLevel.ERROR: ("ctfa.lint.level.error", "✕"),
        SeverityLevel.WARNING: ("ctfa.lint.level.warning", "⚠"),
        SeverityLevel.INFO: ("ctfa.lint.level.info", "🛈"),
    }

    def __init__(
        self,
        challenge_path: Path,
        result: LintResult,
        show_skipped: bool = False,
        show_ignored: bool = False,
        show_passed: bool = False,
    ):
        self.challenge_path = challenge_path
        self.result = result
        self.show_skipped = show_skipped
        self.show_ignored = show_ignored
        self.show_passed = show_passed

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if not self.result.failed and not self.result.errors:
            result_tree = Tree(f"{self.challenge_path.name} (No issues found)")
        else:
            root_label = self.challenge_path.name
            highest_severity = SeverityLevel.INFO
            if self.result.failed and self.result.errors:
                root_label = f"{self.challenge_path.name} ({len(self.result.failed)} violations, {len(self.result.errors)} errors)"
                highest_severity = SeverityLevel.FATAL
            elif self.result.failed:
                root_label = f"{self.challenge_path.name} ({len(self.result.failed)} violations)"
            elif self.result.errors:
                root_label = f"{self.challenge_path.name} ({len(self.result.errors)} errors)"
                highest_severity = SeverityLevel.FATAL

            result_tree = Tree(root_label)

            for error in self.result.errors:
                result_tree.add(
                    f"✕ ERROR - {error.code} - {error.message}",
                    style="ctfa.lint.error",
                )

            for failed in self.result.failed:
                if highest_severity is None or failed.level > highest_severity:
                    highest_severity = failed.level

                style, icon = self.VIOLATION_STYLES[failed.level]

                result_tree.add(
                    f"{icon} {failed.level.name} - {failed.code} - {failed.message}",
                    style=style,
                )

            result_tree.style = self.VIOLATION_STYLES[highest_severity][0]

        if self.show_passed and self.result.passed:
            for passed in self.result.passed:
                result_tree.add(
                    f"✔ PASSED - {passed.code}",
                    style="ctfa.lint.passed",
                )

        if self.show_skipped and self.result.skipped:
            for skipped in self.result.skipped:
                result_tree.add(
                    f"⏩ SKIPPED - {skipped.code} - {skipped.message}",
                    style="ctfa.lint.skipped",
                )

        if self.show_ignored and self.result.ignored:
            for ignored in self.result.ignored:
                result_tree.add(
                    f"🚫 IGNORED - {ignored.code} - {ignored.message}",
                    style="ctfa.lint.ignored",
                )

        if len(result_tree.children) == 0:
            result_tree.add("✓ All checks passed", style="ctfa.lint.passed")

        yield Panel(
            result_tree,
            title=f"{self.challenge_path.name} Lint Results",
            style="ctfa.info",
            border_style="green",
        )


class RepoLintResultComponent:
    # SeverityLevel -> (style, icon)
    VIOLATION_STYLES = {
        SeverityLevel.FATAL: ("ctfa.lint.level.fatal", "✕"),
        SeverityLevel.ERROR: ("ctfa.lint.level.error", "✕"),
        SeverityLevel.WARNING: ("ctfa.lint.level.warning", "⚠"),
        SeverityLevel.INFO: ("ctfa.lint.level.info", "🛈"),
    }

    def __init__(
        self,
        results: dict[str, dict[str, LintResult]],
        show_skipped: bool = False,
        show_ignored: bool = False,
        show_passed: bool = False,
    ):
        self.results = results
        self.show_skipped = show_skipped
        self.show_ignored = show_ignored
        self.show_passed = show_passed

    def get_tree_label(self, prefix: str, violations: int, errors: int) -> str:
        label = prefix
        if violations > 0 or errors > 0:
            label += " ("
            if violations > 0:
                label += f"{violations} violations"
            if errors > 0:
                if violations > 0:
                    label += ", "
                label += f"{errors} errors"
            label += ")"
        else:
            label += " (No issues found)"
        return label

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        _failed_challenges = 0
        _total_violations = 0
        _total_errors = 0

        result_tree = Tree("challenges/ (No issues found)")

        for category, category_results in self.results.items():
            _passed: dict[str, LintResult] = {}
            _failed: dict[str, LintResult] = {}

            _violations = 0
            _errors = 0

            for challenge, result in category_results.items():
                if result.failed or result.errors:
                    _failed[challenge] = result
                    _violations += len(result.failed)
                    _errors += len(result.errors)

                    _failed_challenges += 1
                    _total_violations += len(result.failed)
                    _total_errors += len(result.errors)
                else:
                    _passed[challenge] = result

            if not _failed:
                category_tree = result_tree.add(f"{category}/ (No issues found)")

                if not self.show_passed:
                    category_tree.add("✓ All challenges passed", style="ctfa.lint.passed")

            else:
                category_label = self.get_tree_label(f"{category}/", _violations, _errors)

                category_tree = result_tree.add(category_label)

                for challenge, result in _failed.items():
                    challenge_label = self.get_tree_label(challenge, len(result.failed), len(result.errors))
                    challenge_tree = category_tree.add(challenge_label)

                    highest_severity = SeverityLevel.INFO

                    # Always show errors first
                    if result.errors:
                        highest_severity = SeverityLevel.FATAL
                        for error in result.errors:
                            challenge_tree.add(
                                f"✕ ERROR - {error.code} - {error.message}",
                                style="ctfa.lint.fatal",
                            )

                    for failed in result.failed:
                        if failed.level > highest_severity:
                            highest_severity = failed.level

                        style, icon = self.VIOLATION_STYLES[failed.level]
                        challenge_tree.add(
                            f"{icon} {failed.level.name} - {failed.code} - {failed.message}",
                            style=style,
                        )

                    challenge_tree.style = self.VIOLATION_STYLES[highest_severity][0]

            if self.show_passed:
                for challenge, result in _passed.items():
                    challenge_label = self.get_tree_label(challenge, len(result.failed), len(result.errors))
                    challenge_tree = category_tree.add(challenge_label)
                    challenge_tree.add("✓ All checks passed", style="ctfa.lint.passed")

        # Update root label if there are failed challenges
        if _failed_challenges > 0:
            root_label = self.get_tree_label("challenges/", _total_violations, _total_errors)
            result_tree.label = root_label

        yield Panel(
            result_tree,
            title="Repository Lint Results",
            style="ctfa.info",
            border_style="green",
        )
