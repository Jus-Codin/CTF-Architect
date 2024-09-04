from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from ctf_architect.core.lint.rules import RULES, Rule, SeverityLevel
from ctf_architect.core.models import CTFConfig


class RuleViolation(TypedDict):
    code: str
    level: str
    message: str


class LintResult(TypedDict):
    violations: list[RuleViolation]
    ignored: list[str]


class Linter:
    def __init__(
        self,
        ctf_config: CTFConfig | None = None,
        level: SeverityLevel | None = None,
        ignore: list[str] | None = None,
    ):
        self.ctf_config = ctf_config
        self.level = level
        self.ignore = ignore or []

    def process_rule(self, challenge_path: Path, rule: Rule) -> RuleViolation | None:
        if rule.level < self.level:
            return None

        if rule.code in self.ignore:
            return None

        result = rule.check(challenge_path, self.ctf_config)

        if result is not True:
            return {
                "code": rule.code,
                "level": rule.level,
                "message": result if result is not False else rule.message,
            }

        return None

    def lint(self, challenge_path: Path) -> LintResult:
        violations = []

        fatal_rules = [rule for rule in RULES if rule.level == SeverityLevel.FATAL]

        for rule in fatal_rules:
            violation = self.process_rule(challenge_path, rule)
            if violation is not None:
                violations.append(violation)

        if violations:
            return {"violations": violations, "ignored": self.ignore}

        non_fatal_rules = [rule for rule in RULES if rule.level != SeverityLevel.FATAL]

        for rule in non_fatal_rules:
            violation = self.process_rule(challenge_path, rule)
            if violation is not None:
                violations.append(violation)

        return {"violations": violations, "ignored": self.ignore}
