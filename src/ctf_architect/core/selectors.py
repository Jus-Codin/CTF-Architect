from __future__ import annotations

import re
from collections.abc import Callable
from operator import contains, eq, ge, gt, le, lt, ne
from typing import Any

from ctf_architect.core.challenge import Challenge
from ctf_architect.models.deployment import SelectorRule
from ctf_architect.utils import MISSING

_OPERATORS = {
    "==": eq,
    "!=": ne,
    ">": gt,
    "<": lt,
    ">=": ge,
    "<=": le,
}


def _handle_length(field_value: Any, rule_value: int) -> bool:
    try:
        return len(field_value) == rule_value
    except TypeError:
        return False


def _handle_pattern(field_value: Any, rule_value: str) -> bool:
    if not isinstance(field_value, str):
        return False
    return re.match(rule_value, field_value) is not None


def _handle_expression(field_value: Any, rule_value: str) -> bool:
    match = re.match(r"^(==|!=|>=|<=|>|<)\s*(.+)$", rule_value)
    if not match:
        return False

    operator, value_str = match.groups()
    operator_func = _OPERATORS.get(operator)
    if operator_func is None:
        return False

    try:
        if isinstance(field_value, (int | float)):
            value = type(field_value)(value_str)
        elif isinstance(field_value, str):
            value = value_str
        else:
            return False
    except ValueError:
        return False

    return operator_func(field_value, value)


# The normal matchers. Key and exists require some special handling.
MATCHERS: dict[str, Callable[[Any, Any], bool]] = {
    "value": eq,
    "length": _handle_length,
    "contains": contains,
    "pattern": _handle_pattern,
    "expression": _handle_expression,
}


def _resolve_field_value(challenge: Challenge, parts: list[str]) -> Any:
    """Resolves a field value from a challenge given a list of parts."""
    field_value: Any = challenge
    for part in parts:
        if not hasattr(field_value, part):
            return MISSING
        field_value = getattr(field_value, part)
    return field_value


def match_selector_rule(challenge: Challenge, field_name: str, rule: SelectorRule) -> bool:
    """Check if a selector rule matches a challenge.

    Parameters:
        challenge (Challenge): The challenge to check.
        field_name (str): The field name to check.
        rule (SelectorRule): The selector rule to check against.

    Returns:
        bool: True if the challenge matches the rule, False otherwise.
    """
    # Strategy:
    # 1. First parse "key" matcher to check which fields we are checking.
    #    If no key is given, we just use the field_name directly.
    #    If multiple keys are given, we will have to check all of them.
    # 2. Resolve for "exists" matcher first, as it is a special case.
    # 3. Then check all other matchers.

    base = field_name.split(".")

    # Get all possible keys to check
    if rule.key is not None:
        if isinstance(rule.key, str):
            keys = [base + rule.key.split(".")]
        else:
            keys = [base + key.split(".") for key in rule.key]
    else:
        keys = [base]

    for key in keys:
        field_value = _resolve_field_value(challenge, key)

        # Handle "exists" matcher
        # This key is a bit special, as it can actually bypass other matchers.
        if rule.exists is not None:
            # If field does not exist but must exist, instantly fail for this key
            if rule.exists and field_value is MISSING:
                continue
            # If field exists but must not exist, instantly fail for this key
            if not rule.exists and field_value is not MISSING:
                continue

        # If field does not exist, we cannot match any other rules
        if field_value is MISSING:
            continue

        all_match = True
        # Time complexity here is a little worrying
        for matcher_name, matcher_func in MATCHERS.items():
            rule_value = getattr(rule, matcher_name, None)
            if rule_value is not None:
                if isinstance(rule_value, list):
                    if not any(matcher_func(field_value, rv) for rv in rule_value):
                        all_match = False
                        break
                else:
                    if not matcher_func(field_value, rule_value):
                        all_match = False
                        break

        if all_match:
            return True

    return False
