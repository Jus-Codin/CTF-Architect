from pathlib import Path

import pytest
from pydantic import ValidationError

from ctf_architect.models.challenge import Challenge, ChallengeFile, Flag, Hint, Service
from ctf_architect.version import CHALLENGE_SPEC_VERSION


@pytest.mark.parametrize(
    ("flag", "regex", "case_insensitive"),
    [
        ("flag{example_flag}", False, False),
        ("flag{example_flag}", True, False),
        ("flag{example_flag}", False, True),
        ("flag{example_flag}", True, True),
    ],
)
def test_flag_initialization(flag, regex, case_insensitive):
    """Test the Flag model with various flag configurations."""
    if regex is None:
        flag_instance = Flag(flag=flag)

    flag_instance = Flag(flag=flag, regex=regex, case_insensitive=case_insensitive)
    assert flag_instance.flag == flag
    assert flag_instance.regex is regex
    assert flag_instance.case_insensitive is case_insensitive


def test_flag_initialization_defaults():
    """Test the Flag model with default values."""
    flag_instance = Flag(flag="flag{default_flag}")
    assert flag_instance.flag == "flag{default_flag}"
    assert flag_instance.regex is False
    assert flag_instance.case_insensitive is False


def test_hint_initialization():
    """Test the Hint model."""
    hint = Hint(cost=100, content="This is a hint", requirements=[1, 2])
    assert hint.cost == 100
    assert hint.content == "This is a hint"
    assert hint.requirements == [1, 2]


def test_hint_initialization_without_requirements():
    """Test the Hint model without requirements."""
    hint = Hint(cost=50, content="This is another hint")
    assert hint.cost == 50
    assert hint.content == "This is another hint"
    assert hint.requirements is None


@pytest.mark.parametrize(
    ("name", "path", "ports", "type"),
    [
        ("web_service", Path("/path/to/web"), [80], "web"),
        ("tcp_service", Path("/path/to/tcp"), [8080], "tcp"),
        ("ssh_service", Path("/path/to/ssh"), [22], "ssh"),
        ("secret_service", Path("/path/to/secret"), [1337], "secret"),
    ],
)
def test_service_initialization(name, path, ports, type):
    """Test the Service model with various service configurations."""
    service = Service(name=name, path=path, ports=ports, type=type)
    assert service.name == name
    assert service.path == path
    assert service.ports == ports
    assert service.type == type


def test_internal_service_initialization():
    """Test that the Service model can handle internal services with no ports."""
    service = Service(
        name="internal_service",
        path=Path("/path/to/internal"),
        type="internal",
        ports=None,
    )
    assert service.name == "internal_service"
    assert service.path == Path("/path/to/internal")
    assert service.ports is None


@pytest.mark.parametrize(
    "name",
    [
        "valid_service",
        "another-valid_service",
        "valid123",
        "valid-service-1",
        "valid_service_2",
    ],
)
def test_valid_service_names(name):
    """Test that valid service names do not raise validation errors."""
    service = Service(name=name, path=Path("/path/to/service"), type="internal")
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
def test_invalid_service_names(name):
    """Test that invalid service names raise validation errors."""
    with pytest.raises(ValidationError, match="String should match pattern"):
        Service(name=name, path=Path("/path/to/service"), type="internal")


def test_invalid_service_port():
    """Test that a service with a port outside the valid range raises a validation error."""
    with pytest.raises(ValidationError, match="Input should be less than or equal to 65535"):
        Service(name="invalid_port_service", path=Path("/path/to/service"), ports=[70000], type="web")

    with pytest.raises(ValidationError, match="Input should be greater than or equal to 1"):
        Service(name="invalid_port_service", path=Path("/path/to/service"), ports=[0], type="web")


@pytest.mark.parametrize(
    ("service_path", "expected"),
    [
        (Path("/path/to/service"), "/path/to/service"),
        (Path("relative/path/to/service"), "relative/path/to/service"),
        (Path("C:/windows/path/to/service"), "C:/windows/path/to/service"),
        (Path("windows\\relative\\path"), "windows/relative/path"),
    ],
)
def test_service_path_serialization(service_path, expected):
    """Test that the service path is serialized to a POSIX string."""
    service = Service(name="test_service", path=service_path, ports=[8080], type="web")
    serialized = service.model_dump()

    assert serialized["path"] == expected, f"Expected {expected}, got {serialized['path']}"


def test_service_deserialization():
    """Test deserialization of the Service model."""
    service_data = {
        "name": "test_service",
        "path": "/path/to/service",
        "ports": [8080],
        "type": "web",
    }
    service = Service.model_validate(service_data)

    assert service.name == "test_service"
    assert service.path == Path("/path/to/service")
    assert service.ports == [8080]
    assert service.type == "web"
    assert service.extras is None


def test_service_unique_name():
    """Test the unique name generation for a service."""
    challenge = Challenge(
        author="test_author",
        category="test_category",
        description="This is a test challenge",
        difficulty="easy",
        name="test_challenge",
        folder_name="test_challenge",
    )
    service = Service(name="test_service", path=Path("/path/to/service"), ports=[8080], type="web")
    unique_name = service.unique_name(challenge)

    expected_unique_name = "test_category-test_challenge-test_service".lower().replace(" ", "-")
    assert unique_name == expected_unique_name, f"Expected {expected_unique_name}, got {unique_name}"


@pytest.fixture
def challenge_data():
    """Fixture for a sample challenge dictionary."""
    return {
        "author": "test_author",
        "category": "test_category",
        "description": "This is a test challenge",
        "difficulty": "easy",
        "name": "test_challenge",
        "folder_name": "test_challenge",
        "files": ["/path/to/file.txt", "http://example.com/file.txt"],
        "requirements": ["requirement1", "requirement2"],
        "extras": {"test_extra_key": "test_extra_value"},
        "flags": [{"flag": "flag{test_flag}", "regex": False, "case_insensitive": False}],
        "hints": [{"cost": 100, "content": "This is a test hint", "requirements": None}],
        "services": [
            {
                "name": "test_service",
                "path": "/path/to/service",
                "port": None,
                "ports": [8080],
                "type": "web",
                "extras": None,
            }
        ],
    }


def test_challenge_initialization(challenge_data):
    """Test the Challenge model initialization."""
    challenge = Challenge.model_validate(challenge_data)
    assert challenge.author == "test_author"
    assert challenge.category == "test_category"
    assert challenge.description == "This is a test challenge"
    assert challenge.difficulty == "easy"
    assert challenge.name == "test_challenge"
    assert challenge.folder_name == "test_challenge"
    assert challenge.requirements == ["requirement1", "requirement2"]
    assert challenge.extras == {"test_extra_key": "test_extra_value"}

    assert isinstance(challenge.flags, list)
    assert len(challenge.flags) == 1
    assert challenge.flags[0] == Flag(flag="flag{test_flag}")

    assert isinstance(challenge.hints, list)
    assert len(challenge.hints) == 1
    assert challenge.hints[0] == Hint(cost=100, content="This is a test hint")

    assert isinstance(challenge.services, list)
    assert len(challenge.services) == 1
    assert challenge.services[0] == Service(
        name="test_service", path=Path("/path/to/service"), ports=[8080], type="web"
    )


def test_challenge_folder_name_validation():
    """Test that the folder name is validated correctly."""
    with pytest.raises(ValidationError, match="String should match pattern"):
        Challenge(
            author="test_author",
            category="test_category",
            description="This is a test challenge",
            difficulty="easy",
            name="test_challenge",
            folder_name="inv@lid_folder_name",  # Invalid folder name
        )

    # Valid folder name
    challenge = Challenge(
        author="test_author",
        category="test_category",
        description="This is a test challenge",
        difficulty="easy",
        name="test_challenge",
        folder_name="valid_folder_name_123",  # Valid folder name
    )
    assert challenge.folder_name == "valid_folder_name_123"


def test_challenge_ensure_folder_name():
    """Test that the folder name is auto-generated if not provided."""
    with pytest.raises(ValidationError, match="Invalid challenge name, unable to create a valid folder name"):
        Challenge(
            author="test_author",
            category="test_category",
            description="This is a test challenge",
            difficulty="easy",
            name="|{{+",
        )

    # Valid challenge with auto-generated folder name
    challenge = Challenge(
        author="test_author",
        category="test_category",
        description="This is a test challenge",
        difficulty="easy",
        name="🦈Baby Shark",  # Name with invalid characters
    )
    assert challenge.folder_name == "Baby Shark"


@pytest.mark.parametrize(
    ("category", "folder_name", "expected_network_name"),
    [
        ("underscore_category", "underscore_folder", "underscore_category-underscore_folder-network"),
        ("hypen-category", "hypen-folder", "hypen-category-hypen-folder-network"),
        ("space category", "space folder", "space-category-space-folder-network"),
        ("mixed_category", "Mixed Folder", "mixed_category-mixed-folder-network"),
    ],
)
def test_challenge_network_name(category, folder_name, expected_network_name):
    """Test the network name generation for a challenge."""
    challenge = Challenge(
        author="test_author",
        category=category,
        description="This is a test challenge",
        difficulty="easy",
        name="test_challenge",
        folder_name=folder_name,
    )
    assert challenge.network_name == expected_network_name


def test_challenge_repo_path():
    """Test the repo path generation for a challenge."""
    challenge = Challenge(
        author="test_author",
        category="test_category",
        description="This is a test challenge",
        difficulty="easy",
        name="test_challenge",
        folder_name="test_challenge",
    )
    expected_path = Path("challenges") / "test_category" / "test_challenge"
    assert challenge.repo_path == expected_path


@pytest.mark.parametrize(
    ("file", "expected"),
    [
        (Path("/path/to/file.txt"), "/path/to/file.txt"),
        (Path("relative/path/to/file.txt"), "relative/path/to/file.txt"),
        (Path("C:/windows/path/to/file.txt"), "C:/windows/path/to/file.txt"),
        (Path("windows\\relative\\path"), "windows/relative/path"),
        ("http://example.com/file.txt", "http://example.com/file.txt"),
        ("https://example.com/file.txt", "https://example.com/file.txt"),
    ],
)
def test_challenge_files_serialization(file, expected):
    """Test that the files are serialized correctly."""
    challenge = Challenge(
        author="test_author",
        category="test_category",
        description="This is a test challenge",
        difficulty="easy",
        name="test_challenge",
        folder_name="test_challenge",
        files=[file],
    )
    serialized = challenge.model_dump()

    assert serialized["files"] == [expected], f"Expected {expected}, got {serialized['files']}"


def test_challenge_config_file_from_challenge(challenge_data):
    challenge = Challenge.model_validate(challenge_data)
    challenge_file = ChallengeFile.from_challenge(challenge)
    assert challenge_file.version == str(CHALLENGE_SPEC_VERSION)
    assert challenge_file.challenge == challenge


def test_challenge_config_file_serialization(challenge_data):
    """Test serialization of ChallengeFile."""
    challenge = Challenge.model_validate(challenge_data)
    challenge_file = ChallengeFile.from_challenge(challenge)
    serialized = challenge_file.model_dump()

    assert isinstance(serialized, dict)
    assert serialized == {
        "version": str(CHALLENGE_SPEC_VERSION),
        "challenge": challenge_data,
    }


def test_challenge_config_file_deserialization(challenge_data):
    challenge_file_json = {
        "version": str(CHALLENGE_SPEC_VERSION),
        "challenge": challenge_data,
    }
    challenge_file = ChallengeFile.model_validate(challenge_file_json)
    assert challenge_file.version == str(CHALLENGE_SPEC_VERSION)
    assert challenge_file.challenge == Challenge.model_validate(challenge_data)


def test_challenge_config_file_invalid_version(challenge_data):
    """Test that an invalid version raises a validation error."""
    challenge_file_json = {
        "version": "99.99",  # Invalid version
        "challenge": challenge_data,
    }
    with pytest.raises(ValidationError, match="Unsupported Challenge specification version"):
        ChallengeFile.model_validate(challenge_file_json)
