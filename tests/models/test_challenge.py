from pathlib import Path

import pytest
from pydantic import ValidationError

from ctfa.models.challenge import (
    ChallengeConfig,
    ChallengeConfigFile,
    ChallengeService,
    RegexFlag,
    StaticFile,
    StaticFlag,
    URLFile,
)
from ctfa.version import CHALLENGE_SPEC_VERSION


def test_static_file_ensure_type():
    static_file = StaticFile(path=Path("static/file.txt"))
    serialized = static_file.model_dump()
    assert serialized["type"] == "static"
    assert serialized["path"] == "static/file.txt"


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        (Path("/path/to/file.txt"), "/path/to/file.txt"),
        (Path("relative/path/to/file.txt"), "relative/path/to/file.txt"),
        (Path("C:/windows/path/to/file.txt"), "C:/windows/path/to/file.txt"),
        (Path("windows\\relative\\path"), "windows/relative/path"),
    ],
)
def test_challenge_file_path_serialization(file_path, expected):
    static_file = StaticFile(path=file_path)
    serialized = static_file.model_dump()
    assert serialized["path"] == expected


def test_url_file_ensure_type():
    url_file = URLFile(url="https://example.com/file.txt")  # type: ignore
    serialized = url_file.model_dump()
    assert serialized["type"] == "url"
    assert serialized["url"] == "https://example.com/file.txt"


def test_challenge_config_minimal():
    config = ChallengeConfig(
        id="test-challenge",
        name="Test Challenge",
        description="A test challenge",
        category="misc",
        difficulty="easy",
        author="Test Author",
    )
    serialized = config.model_dump()
    assert serialized["id"] == "test-challenge"
    assert serialized["name"] == "Test Challenge"
    assert serialized["description"] == "A test challenge"
    assert serialized["category"] == "misc"
    assert serialized["difficulty"] == "easy"
    assert serialized["author"] == "Test Author"


def test_challenge_default_folder_name():
    config = ChallengeConfig(
        id="test-challenge",
        name="_@!/",
        description="A test challenge",
        category="misc",
        difficulty="easy",
        author="Test Author",
    )
    assert config.folder_name == config.id


@pytest.mark.parametrize(
    ("type", "name", "ports"),
    [
        ("web", "web_service", [80]),
        ("tcp", "tcp_service", [1337]),
        ("ssh", "ssh_service", [22]),
        ("secret", "secret_service", [1000]),
        ("internal", "internal_service", None),
    ],
)
def test_service_initialization(type, name, ports):
    service = ChallengeService(
        type=type,
        name=name,
        path=Path(f"/services/{name}"),
        ports=ports if ports is not None else [],
    )
    assert service.type == type
    assert service.name == name
    assert service.path == Path(f"/services/{name}")
    assert service.ports == (ports if ports is not None else [])


@pytest.mark.parametrize(
    "name",
    [
        "valid-name",
        "another_valid_name",
        "name123",
        "name-with-dashes",
        "name_with_underscores",
    ],
)
def test_valid_service_names(name):
    service = ChallengeService(
        type="internal",
        name=name,
        path=Path("/path/to/service"),
    )  # type: ignore
    assert service.name == name


@pytest.mark.parametrize(
    "name",
    [
        "Invalid Service",  # Contains space
        "invalid@service",  # Contains invalid character '@'
        "123invalid",  # Starts with a number
        "_invalid",  # Starts with an underscore
    ],
)
def test_invalid_service_name(name):
    with pytest.raises(ValidationError, match="String should match pattern"):
        ChallengeService(
            type="internal",
            name=name,
            path=Path("/path/to/service"),
        )  # type: ignore


def test_invalid_service_port():
    with pytest.raises(ValidationError, match="Input should be less than or equal to 65535"):
        ChallengeService(
            type="web",
            name="web_service",
            path=Path("/path/to/service"),
            ports=[70000],
        )  # type: ignore
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 1"):
        ChallengeService(
            type="web",
            name="web_service",
            path=Path("/path/to/service"),
            ports=[0],
        )  # type: ignore


def test_invalid_service_no_ports():
    with pytest.raises(ValidationError, match="Ports must be specified for non-internal services"):
        ChallengeService(
            type="tcp",
            name="tcp_service",
            path=Path("/path/to/service"),
            ports=[],
        )  # type: ignore


def test_service_unique_name():
    challenge = ChallengeConfig(
        id="unique-challenge",
        name="Unique Challenge",
        description="A unique challenge",
        category="pwn",
        difficulty="medium",
        author="Unique Author",
        folder_name="unique-challenge-folder",
    )
    service = ChallengeService(
        type="tcp",
        name="main_service",
        path=Path("/services/main_service"),
        ports=[4444],
    )
    unique_name = service.unique_name(challenge)
    assert unique_name == "pwn-unique-challenge-main_service"


@pytest.fixture
def raw_challenge_data():
    return {
        "id": "full-challenge",
        "name": "Full Challenge",
        "description": "A full challenge with all fields",
        "category": "crypto",
        "difficulty": "hard",
        "author": "Full Author",
        "folder_name": "full-challenge-folder",
        "requirements": ["req1", "req2"],
        "files": [
            {"type": "static", "path": "files/file1.txt"},
            {"type": "url", "url": "https://example.com/file2.txt"},
        ],
        "flags": [
            {"type": "static", "value": "flag{static_flag}", "case_sensitive": True},
            {"type": "regex", "pattern": "flag\\{[a-zA-Z0-9_]+\\}"},
        ],
        "hints": [
            {
                "cost": 10,
                "content": "This is a hint.",
                "requirements": None,
            },
            {"cost": 20, "content": "This is another hint with requirements.", "requirements": [0]},
        ],
        "extra_labels": {
            "string_label": "example",
            "number_label": 42,
            "bool_label": True,
            "float_label": 3.14,
        },
        "annotations": {
            "sample_annotation": "This is a sample annotation.",
            "nested_annotation": {"key": "value"},
        },
        "services": [
            {
                "type": "web",
                "name": "web_service",
                "path": "services/web_service",
                "ports": [8080],
                "networks": ["net1"],
                "annotations": {"note": "This is a web service."},
            },
            {
                "type": "internal",
                "name": "internal_service",
                "path": "services/internal_service",
                "ports": [],
                "networks": None,
                "annotations": None,
            },
        ],
        "networks": {
            "net1": {"internal": False},
            "net2": {"internal": True},
        },
    }


def test_full_challenge_config(raw_challenge_data):
    challenge = ChallengeConfig.model_validate(raw_challenge_data)
    assert challenge.id == "full-challenge"
    assert challenge.name == "Full Challenge"
    assert challenge.description == "A full challenge with all fields"
    assert challenge.category == "crypto"
    assert challenge.difficulty == "hard"
    assert challenge.author == "Full Author"
    assert challenge.folder_name == "full-challenge-folder"
    assert challenge.requirements == ["req1", "req2"]

    assert isinstance(challenge.files, list)
    assert len(challenge.files) == 2
    assert isinstance(challenge.files[0], StaticFile)
    assert challenge.files[0].path == Path("files/file1.txt")
    assert isinstance(challenge.files[1], URLFile)
    assert str(challenge.files[1].url) == "https://example.com/file2.txt"

    assert isinstance(challenge.flags, list)
    assert len(challenge.flags) == 2
    assert isinstance(challenge.flags[0], StaticFlag)
    assert challenge.flags[0].value == "flag{static_flag}"
    assert isinstance(challenge.flags[1], RegexFlag)
    assert challenge.flags[1].pattern == r"flag\{[a-zA-Z0-9_]+\}"

    assert isinstance(challenge.hints, list)
    assert len(challenge.hints) == 2
    assert challenge.hints[0].cost == 10
    assert challenge.hints[0].content == "This is a hint."
    assert challenge.hints[1].cost == 20
    assert challenge.hints[1].content == "This is another hint with requirements."
    assert challenge.hints[1].requirements == [0]

    assert isinstance(challenge.extra_labels, dict)
    assert challenge.extra_labels["string_label"] == "example"
    assert challenge.extra_labels["number_label"] == 42
    assert challenge.extra_labels["bool_label"] is True
    assert challenge.extra_labels["float_label"] == 3.14

    assert isinstance(challenge.annotations, dict)
    assert challenge.annotations["sample_annotation"] == "This is a sample annotation."
    assert challenge.annotations["nested_annotation"] == {"key": "value"}

    assert isinstance(challenge.services, list)
    assert len(challenge.services) == 2
    web_service = challenge.services[0]
    assert web_service.type == "web"
    assert web_service.name == "web_service"
    assert web_service.path == Path("services/web_service")
    assert web_service.ports == [8080]
    assert web_service.networks == ["net1"]
    assert web_service.annotations == {"note": "This is a web service."}
    internal_service = challenge.services[1]
    assert internal_service.type == "internal"
    assert internal_service.name == "internal_service"
    assert internal_service.path == Path("services/internal_service")
    assert internal_service.ports == []
    assert internal_service.networks is None
    assert internal_service.annotations is None

    assert isinstance(challenge.networks, dict)
    assert len(challenge.networks) == 2
    assert challenge.networks["net1"].internal is False
    assert challenge.networks["net2"].internal is True


@pytest.mark.parametrize(
    ("category", "expected_network_name"),
    [
        ("underscore_category", "underscore_category-test-id-default"),
        ("hyphen-category", "hyphen-category-test-id-default"),
        ("space category", "space-category-test-id-default"),
        ("Mixed-Category_Name", "mixed-category_name-test-id-default"),
    ],
)
def test_challenge_default_network_name(category, expected_network_name):
    challenge = ChallengeConfig(
        id="test-id",
        name="Test Challenge",
        description="A test challenge",
        category=category,
        difficulty="easy",
        author="Test Author",
    )
    assert challenge.default_network_name == expected_network_name


def test_challenge_repository_path():
    challenge = ChallengeConfig(
        id="test-challenge",
        name="Test Challenge",
        description="A test challenge",
        category="misc",
        difficulty="easy",
        author="Test Author",
        folder_name="test-challenge-folder",
    )
    expected_path = Path("challenges") / "misc" / "test-challenge-folder"
    assert challenge.repository_path == expected_path


def test_challenge_config_file_from_challenge(raw_challenge_data):
    challenge = ChallengeConfig.model_validate(raw_challenge_data)
    challenge_file = ChallengeConfigFile.from_challenge(challenge)
    assert challenge_file.version == str(CHALLENGE_SPEC_VERSION)
    assert challenge_file.challenge == challenge


def test_challenge_config_file_serialization(raw_challenge_data):
    challenge = ChallengeConfig.model_validate(raw_challenge_data)
    challenge_file = ChallengeConfigFile.from_challenge(challenge)
    serialized = challenge_file.model_dump(mode="json")

    assert isinstance(serialized, dict)
    assert serialized == {
        "version": str(CHALLENGE_SPEC_VERSION),
        "challenge": raw_challenge_data,
    }


def test_challenge_config_file_deserialization(raw_challenge_data):
    raw_data = {
        "version": str(CHALLENGE_SPEC_VERSION),
        "challenge": raw_challenge_data,
    }
    challenge_file = ChallengeConfigFile.model_validate(raw_data)
    assert challenge_file.version == str(CHALLENGE_SPEC_VERSION)
    assert challenge_file.challenge == ChallengeConfig.model_validate(raw_challenge_data)


def test_challenge_config_file_invalid_version(raw_challenge_data):
    raw_data = {
        "version": "99.99",
        "challenge": raw_challenge_data,
    }
    with pytest.raises(ValidationError, match="Unsupported Challenge specification version"):
        ChallengeConfigFile.model_validate(raw_data)
