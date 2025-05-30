import pytest
from pydantic import ValidationError

from ctf_architect.models.port_mapping import PortMapping, PortMappingFile
from ctf_architect.version import PORT_MAPPING_SPEC_VERSION


@pytest.mark.parametrize(
    ("from_port", "to_port"),
    [
        (80, 8080),
        (443, None),
    ],
)
def test_port_mapping_initialization(from_port, to_port):
    """Test the PortMapping model with various port mappings."""
    mapping = PortMapping(from_port=from_port, to_port=to_port)
    assert mapping.from_port == from_port
    assert mapping.to_port == to_port


@pytest.fixture
def port_mapping_data():
    """Fixture for a sample port mapping dictionary."""
    return {
        "service-1": [PortMapping(from_port=80, to_port=8080)],
        "service-2": [PortMapping(from_port=22, to_port=None)],
    }


def test_port_mapping_file_from_mapping(port_mapping_data):
    """Test the PortMappingFile model."""
    mapping_file = PortMappingFile.from_mapping(port_mapping_data)
    assert mapping_file.version == str(PORT_MAPPING_SPEC_VERSION)
    assert mapping_file.mapping == port_mapping_data


def test_port_mapping_file_serialization(port_mapping_data):
    """Test serialization of PortMappingFile."""
    mapping_file = PortMappingFile.from_mapping(port_mapping_data)
    serialized = mapping_file.model_dump()

    assert isinstance(serialized, dict)
    assert serialized == {
        "version": str(PORT_MAPPING_SPEC_VERSION),
        "mapping": {
            "service-1": [{"from_port": 80, "to_port": 8080}],
            "service-2": [{"from_port": 22, "to_port": None}],
        },
    }


def test_port_mapping_file_deserialization():
    port_mapping_file_json = {
        "version": str(PORT_MAPPING_SPEC_VERSION),
        "mapping": {
            "service-1": [{"from_port": 80, "to_port": 8080}],
            "service-2": [{"from_port": 22, "to_port": None}],
        },
    }
    mapping_file = PortMappingFile.model_validate(port_mapping_file_json)
    assert mapping_file.version == str(PORT_MAPPING_SPEC_VERSION)
    assert "service-1" in mapping_file.mapping
    assert mapping_file.mapping["service-1"][0].from_port == 80
    assert mapping_file.mapping["service-1"][0].to_port == 8080
    assert "service-2" in mapping_file.mapping
    assert mapping_file.mapping["service-2"][0].from_port == 22
    assert mapping_file.mapping["service-2"][0].to_port is None


def test_port_mapping_file_invalid_version():
    """Test that an invalid version raises a validation error."""
    with pytest.raises(ValidationError, match="Unsupported Port Mapping specification version"):
        PortMappingFile.model_validate({"version": "99.99", "mapping": {}})
