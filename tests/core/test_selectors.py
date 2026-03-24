from ctfa.core.workflow.selectors import challenge_matches_selectors, filter_challenges
from ctfa.models.challenge import ChallengeConfig
from ctfa.models.workflow import Selectors


def _challenge(
    challenge_id: str,
    *,
    category: str,
    difficulty: str,
    requirements: list[str] | None = None,
    extra_labels: dict[str, str] | None = None,
) -> ChallengeConfig:
    return ChallengeConfig(
        id=challenge_id,
        name=challenge_id,
        description="Test challenge",
        category=category,
        difficulty=difficulty,
        author="tester",
        requirements=requirements,
        extra_labels=extra_labels,
    )


def test_selector_include_all_with_exclusion():
    crypto = _challenge("crypto-1", category="crypto", difficulty="easy")
    web = _challenge("web-1", category="web", difficulty="easy")

    selectors = Selectors(include="*", exclude=[{"category": {"value": "web"}}])
    selected = filter_challenges([crypto, web], selectors)

    assert [challenge.id for challenge in selected] == ["crypto-1"]


def test_selector_rule_level_or_behavior():
    crypto_hard = _challenge("crypto-hard", category="crypto", difficulty="hard")
    web_easy = _challenge("web-easy", category="web", difficulty="easy")
    pwn_hard = _challenge("pwn-hard", category="pwn", difficulty="hard")

    selectors = Selectors(
        include=[
            {"category": {"value": "crypto"}},
            {"difficulty": {"value": "easy"}},
        ]
    )

    selected = filter_challenges([crypto_hard, web_easy, pwn_hard], selectors)
    assert [challenge.id for challenge in selected] == ["crypto-hard", "web-easy"]


def test_selector_field_level_and_behavior():
    crypto_easy = _challenge("crypto-easy", category="crypto", difficulty="easy")
    crypto_hard = _challenge("crypto-hard", category="crypto", difficulty="hard")

    selectors = Selectors(include=[{"category": {"value": "crypto"}, "difficulty": {"value": "easy"}}])

    assert challenge_matches_selectors(crypto_easy, selectors) is True
    assert challenge_matches_selectors(crypto_hard, selectors) is False


def test_selector_matchers_contains_pattern_length_key_exists():
    challenge = _challenge(
        "crypto-special",
        category="crypto",
        difficulty="easy",
        requirements=["starter", "warmup"],
        extra_labels={"tier": "gold", "owner": "blue-team"},
    )

    selectors = Selectors(
        include=[
            {
                "id": {"pattern": "^crypto-"},
                "requirements": {"contains": "starter", "length": 2},
                "extra_labels": {"key": "tier", "value": "gold", "exists": True},
            }
        ]
    )

    assert challenge_matches_selectors(challenge, selectors) is True


def test_selector_exists_false_for_missing_field():
    challenge = _challenge("misc-1", category="misc", difficulty="easy")
    selectors = Selectors(include=[{"extra_labels": {"key": "owner", "exists": False}}])

    assert challenge_matches_selectors(challenge, selectors) is True
