from __future__ import annotations

from pydantic import field_validator

from ctf_architect.models.base import Model
from ctf_architect.version import PORT_MAPPING_SPEC_VERSION, is_supported_port_mapping_version


class PortMapping(Model):
    """Represents a port mapping for a service.

    Attributes:
        from_port (int): The starting port for the mapping.
        to_port (int | None): The ending port for the mapping.
    """

    from_port: int
    to_port: int | None


class PortMappingFile(Model):
    """Represents a port_mapping.json file.

    Attributes:
        version (str): The specification version.
        mapping (dict[str, list[PortMapping]]): The port mapping object.
    """

    version: str
    mapping: dict[str, list[PortMapping]]

    @field_validator("version")
    def _validate_version(cls, value: str) -> str:
        if not is_supported_port_mapping_version(value):
            raise ValueError(
                f'Unsupported Port Mapping specification version: "{value}", current version "{PORT_MAPPING_SPEC_VERSION}"'
            )
        return value

    @classmethod
    def from_mapping(cls, mapping: dict[str, list[PortMapping]]) -> PortMappingFile:
        """Create a PortMappingFile object from a port mapping object.

        Args:
            mapping (dict[str, list[PortMapping]]): The port mapping object to convert.

        Returns:
            PortMappingFile: The converted PortMappingFile object.
        """
        return cls(version=str(PORT_MAPPING_SPEC_VERSION), mapping=mapping)
