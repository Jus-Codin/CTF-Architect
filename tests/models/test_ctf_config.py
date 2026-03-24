import pytest

from ctfa.models.ctf_config import CTFConfig, ExtraLabelConfig, RepositoryConfigFile
from ctfa.version import CTF_CONFIG_SPEC_VERSION


def test_extra_label_initialization():
    extra_label = ExtraLabelConfig(
        name="example_label",
        description="An example extra label",
        prompt="Please provide an example value",
        required=True,
        type="string",
    )
    assert extra_label.name == "example_label"
    assert extra_label.description == "An example extra label"
    assert extra_label.prompt == "Please provide an example value"
    assert extra_label.required is True
    assert extra_label.type == "string"


@pytest.fixture
def raw_ctf_config_data():
    return {
        "name": "Example CTF",
        "categories": ["web", "crypto"],
        "difficulties": ["easy", "medium", "hard"],
        "flag_format": "flag{.*}",
        "starting_port": 10000,
        "extra_labels": [
            {
                "name": "example_label",
                "description": "An example extra label",
                "prompt": "Please provide an example value",
                "required": True,
                "type": "string",
            }
        ],
    }


def test_ctf_config_initialization(raw_ctf_config_data):
    config = CTFConfig.model_validate(raw_ctf_config_data)
    assert config.name == "Example CTF"
    assert config.categories == ["web", "crypto"]
    assert config.difficulties == ["easy", "medium", "hard"]
    assert config.flag_format == "flag{.*}"
    assert config.starting_port == 10000

    assert isinstance(config.extra_labels, list)
    assert len(config.extra_labels) == 1

    extra_label = config.extra_labels[0]
    assert isinstance(extra_label, ExtraLabelConfig)
    assert extra_label.name == "example_label"
    assert extra_label.description == "An example extra label"
    assert extra_label.prompt == "Please provide an example value"
    assert extra_label.required is True
    assert extra_label.type == "string"


def test_ctf_config_categories_to_lower(raw_ctf_config_data):
    raw_ctf_config_data["categories"] = ["Web", "CRYPTO"]
    config = CTFConfig.model_validate(raw_ctf_config_data)
    assert config.categories == ["web", "crypto"]


def test_repository_config_file_from_config(raw_ctf_config_data):
    config = CTFConfig.model_validate(raw_ctf_config_data)
    config_file = RepositoryConfigFile.from_ctf_config(config)

    assert config_file.version == str(CTF_CONFIG_SPEC_VERSION)
    assert config_file.config == config


def test_repository_config_file_serialization(raw_ctf_config_data):
    config = CTFConfig.model_validate(raw_ctf_config_data)
    config_file = RepositoryConfigFile.from_ctf_config(config)

    serialized = config_file.model_dump()
    expected = {
        "version": str(CTF_CONFIG_SPEC_VERSION),
        "config": raw_ctf_config_data,
    }

    assert serialized == expected


def test_repository_config_file_deserialization(raw_ctf_config_data):
    data = {
        "version": str(CTF_CONFIG_SPEC_VERSION),
        "config": raw_ctf_config_data,
    }

    config_file = RepositoryConfigFile.model_validate(data)
    assert config_file.version == str(CTF_CONFIG_SPEC_VERSION)
    assert config_file.config == CTFConfig.model_validate(raw_ctf_config_data)


def test_ctf_config_file_invalid_version(raw_ctf_config_data):
    data = {
        "version": "99.99",
        "config": raw_ctf_config_data,
    }

    with pytest.raises(ValueError, match='Unsupported CTF Config specification version: "99.99"'):
        RepositoryConfigFile.model_validate(data)
