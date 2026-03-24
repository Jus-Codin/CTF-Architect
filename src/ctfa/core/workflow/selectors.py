from __future__ import annotations

import re
from collections.abc import Iterable
from operator import contains, eq
from typing import Any

from ctfa.models.challenge import ChallengeConfig
from ctfa.models.workflow import SelectorRule, Selectors
from ctfa.utils import MISSING


def _resolve_field_value(obj: Any, parts: list[str]) -> Any:
    field_value = obj

    for part in parts:
        if isinstance(field_value, dict):
            if part not in field_value:
                return MISSING
            field_value = field_value[part]
            continue

        if not hasattr(field_value, part):
            return MISSING
        field_value = getattr(field_value, part)

    return field_value


def _handle_length(field_value: Any, rule_value: int) -> bool:
    try:
        return len(field_value) == rule_value
    except TypeError:
        return False


def _handle_pattern(field_value: Any, rule_value: str) -> bool:
    if not isinstance(field_value, str):
        return False
    return re.search(rule_value, field_value) is not None


MATCHERS = {
    "value": eq,
    "length": _handle_length,
    "contains": contains,
    "pattern": _handle_pattern,
}


def match_selector_rule(challenge: ChallengeConfig, field_name: str, rule: SelectorRule) -> bool:
    base = field_name.split(".")
    has_additional_matchers = any(getattr(rule, matcher_name) is not None for matcher_name in MATCHERS)

    if rule.key is not None:
        if isinstance(rule.key, str):
            keys = [base + rule.key.split(".")]
        else:
            keys = [base + key.split(".") for key in rule.key]
    else:
        keys = [base]

    for key in keys:
        field_value = _resolve_field_value(challenge, key)

        if rule.exists is not None:
            if rule.exists and field_value is MISSING:
                continue
            if not rule.exists and field_value is MISSING and not has_additional_matchers:
                return True
            if not rule.exists and field_value is not MISSING:
                continue

        if field_value is MISSING:
            continue

        all_match = True
        for matcher_name, matcher_func in MATCHERS.items():
            rule_value = getattr(rule, matcher_name)
            if rule_value is None:
                continue

            if isinstance(rule_value, list):
                if not any(matcher_func(field_value, candidate) for candidate in rule_value):
                    all_match = False
                    break
            elif not matcher_func(field_value, rule_value):
                all_match = False
                break

        if all_match:
            return True

    return False


def _matches_rule_set(challenge: ChallengeConfig, rule_set: dict[str, SelectorRule]) -> bool:
    return all(match_selector_rule(challenge, field_name, rule) for field_name, rule in rule_set.items())


def challenge_matches_selectors(challenge: ChallengeConfig, selectors: Selectors | None) -> bool:
    if selectors is None:
        return True

    if selectors.include == "*":
        is_included = True
    elif selectors.include is None:
        is_included = False
    else:
        is_included = any(_matches_rule_set(challenge, rule_set) for rule_set in selectors.include)

    if not is_included:
        return False

    if selectors.exclude == "*":
        return False

    if selectors.exclude is None:
        return True

    is_excluded = any(_matches_rule_set(challenge, rule_set) for rule_set in selectors.exclude)
    return not is_excluded


def filter_challenges(challenges: Iterable[ChallengeConfig], selectors: Selectors | None) -> list[ChallengeConfig]:
    return [challenge for challenge in challenges if challenge_matches_selectors(challenge, selectors)]
