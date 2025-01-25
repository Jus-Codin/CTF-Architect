"""Exception classes for CTF Architect."""


class InvalidCategoryError(Exception):
    """Raised when an invalid category is provided."""

    pass


class InvalidChallengeFolderError(Exception):
    """Raised when an invalid challenge folder is provided."""

    pass


class ChallengeExistsError(Exception):
    """Raised when a challenge already exists."""

    pass


class FolderNameCollisionError(Exception):
    """Raised when a folder name collision occurs."""

    pass


class NotInChallengeRepositoryError(Exception):
    """Raised when an action is performed outside of a challenge repository when it is not allowed."""

    pass


class MissingStartingPortError(Exception):
    """Raised when a starting port is missing from the config file."""

    pass


class DuplicateServiceNameError(Exception):
    """Raised when a duplicate service name is found."""

    pass


class InvalidPortMappingError(Exception):
    """Raised when an invalid port mapping is provided."""

    pass


class DuplicateRuleCodeError(Exception):
    """Raised when a duplicate rule code is found."""

    pass
