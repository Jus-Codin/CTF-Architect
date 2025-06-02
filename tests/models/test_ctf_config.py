import pytest

from ctf_architect.models.ctf_config import ConfigFile, CTFConfig, ExtraField
from ctf_architect.version import CTF_CONFIG_SPEC_VERSION


def test_extra_field_initialization():
    """Test the ExtraField model."""
    extra_field = ExtraField(
        name="example_field",
        description="An example extra field",
        prompt="Please provide an example value",
        required=True,
        type="string",
    )
    assert extra_field.name == "example_field"
    assert extra_field.description == "An example extra field"
    assert extra_field.prompt == "Please provide an example value"
    assert extra_field.required is True
    assert extra_field.type == "string"


@pytest.fixture
def ctf_config_data():
    """Fixture for a sample CTF config dictionary."""
    return {
        "categories": ["web", "crypto"],
        "difficulties": ["easy", "medium", "hard"],
        "flag_format": "flag{.*}",
        "starting_port": 10000,
        "name": "Example CTF",
        "extras": [
            {
                "name": "example_field",
                "description": "An example extra field",
                "prompt": "Please provide an example value",
                "required": True,
                "type": "string",
            }
        ],
    }


def test_ctf_config_initialization(ctf_config_data):
    """Test the CTFConfig model."""
    config = CTFConfig.model_validate(ctf_config_data)
    assert config.categories == ["web", "crypto"]
    assert config.difficulties == ["easy", "medium", "hard"]
    assert config.flag_format == "flag{.*}"
    assert config.starting_port == 10000
    assert config.name == "Example CTF"

    assert isinstance(config.extras, list)
    assert len(config.extras) == 1

    assert isinstance(config.extras[0], ExtraField)
    assert config.extras[0].name == "example_field"
    assert config.extras[0].description == "An example extra field"
    assert config.extras[0].prompt == "Please provide an example value"
    assert config.extras[0].required is True
    assert config.extras[0].type == "string"


def test_ctf_config_categories_to_lower(ctf_config_data):
    """Test that categories are converted to lowercase."""
    ctf_config_data["categories"] = ["Web", "Crypto"]
    config = CTFConfig.model_validate(ctf_config_data)
    assert config.categories == ["web", "crypto"]


def test_ctf_config_file_from_config(ctf_config_data):
    """Test creating a CTFConfig object from a CTFConfig."""
    config = CTFConfig.model_validate(ctf_config_data)
    config_file = ConfigFile.from_ctf_config(config)

    assert config_file.version == str(CTF_CONFIG_SPEC_VERSION)
    assert config_file.config == config


def test_ctf_config_file_serialization(ctf_config_data):
    """Test serialization of ConfigFile."""
    config = CTFConfig.model_validate(ctf_config_data)
    config_file = ConfigFile.from_ctf_config(config)
    serialized = config_file.model_dump()

    assert isinstance(serialized, dict)
    assert serialized == {
        "version": str(CTF_CONFIG_SPEC_VERSION),
        "config": ctf_config_data,
    }


def test_ctf_config_file_deserialization(ctf_config_data):
    """Test deserialization of ConfigFile."""
    config_file_json = {
        "version": str(CTF_CONFIG_SPEC_VERSION),
        "config": ctf_config_data,
    }
    config_file = ConfigFile.model_validate(config_file_json)
    assert config_file.version == str(CTF_CONFIG_SPEC_VERSION)
    assert config_file.config == CTFConfig.model_validate(ctf_config_data)


def test_ctf_config_file_invalid_version(ctf_config_data):
    """Test that an invalid version raises a ValueError."""
    config_file_json = {
        "version": "99.99",  # Invalid version
        "config": ctf_config_data,
    }
    with pytest.raises(ValueError, match="Unsupported CTF Config specification version"):
        ConfigFile.model_validate(config_file_json)
