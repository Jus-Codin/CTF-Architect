"""Custom exceptions for CTF Architect core operations."""

from __future__ import annotations

from pathlib import Path


class CTFArchitectError(Exception):
    """Base exception for all CTF Architect errors."""


class CategoryNotFoundError(CTFArchitectError):
    """Raised when a specified category does not exist in the CTF config."""

    def __init__(self, category: str):
        self.category = category
        super().__init__(f"Category '{category}' does not exist in the CTF config.")


class ChallengeExistsError(CTFArchitectError):
    """Raised when a challenge with the same ID already exists in the repository."""

    def __init__(self, challenge_id: str, existing_path: str | Path):
        self.challenge_id = challenge_id
        self.existing_path = existing_path
        super().__init__(f"A challenge with ID '{challenge_id}' already exists in the repository at '{existing_path}'.")


class FolderNameCollisionError(CTFArchitectError):
    """Raised when a folder name is already used by a different challenge."""

    def __init__(self, existing_id: str, new_id: str, folder_path: str | Path):
        self.existing_id = existing_id
        self.new_id = new_id
        self.folder_path = folder_path
        super().__init__(
            f"Another challenge is using the same folder name. Please resolve the conflict.\n"
            f"Existing challenge ID: {existing_id}, New challenge ID: {new_id} "
            f"at folder '{folder_path}'."
        )


class ChallengeNotFoundError(CTFArchitectError):
    """Raised when a challenge cannot be found in the repository."""

    def __init__(self, identifier: str, identifier_type: str = "ID"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        super().__init__(f"No challenge with {identifier_type} '{identifier}' found in the repository.")


class InvalidChallengeRepositoryError(CTFArchitectError):
    """Raised when a path is not a valid challenge repository."""

    def __init__(self, path: str | Path):
        self.path = path
        super().__init__(f"The specified path '{path}' is not a valid Challenge Repository.")


class InvalidChallengeFolderError(CTFArchitectError):
    """Raised when a path is not a valid challenge folder."""

    def __init__(self, path: str | Path):
        self.path = path
        super().__init__(f"The specified path '{path}' is not a valid challenge folder.")


class ConfigFileNotFoundError(CTFArchitectError):
    """Raised when a config file cannot be found."""

    def __init__(self, path: str | Path, config_type: str = "config"):
        self.path = path
        self.config_type = config_type
        super().__init__(f"No {config_type} file found in {path}")


class PathExistsAsFileError(CTFArchitectError):
    """Raised when a path exists but is a file when a directory is expected."""

    def __init__(self, path: str | Path):
        self.path = path
        super().__init__(f"The specified path '{path}' exists and is not a directory.")


class PathIsNotDirectoryError(CTFArchitectError):
    """Raised when a path is not a directory."""

    def __init__(self, path: str | Path):
        self.path = path
        super().__init__(f"The specified folder '{path}' is not a directory.")


class DestinationExistsError(CTFArchitectError):
    """Raised when a destination path already exists."""

    def __init__(self, path: str | Path, reason: str = "is an existing file"):
        self.path = path
        self.reason = reason
        super().__init__(f"The specified destination '{path}' {reason}.")


class ChallengePathExistsError(CTFArchitectError):
    """Raised when a challenge path already exists."""

    def __init__(self, path: str | Path, reason: str = "is an existing file"):
        self.path = path
        self.reason = reason
        super().__init__(f"The specified challenge path '{path}' {reason}.")


class InvalidParameterError(CTFArchitectError):
    """Raised when invalid parameters are provided."""

    def __init__(self, message: str):
        super().__init__(message)


class FileNotFoundInChallengeError(CTFArchitectError):
    """Raised when a required file is not found in a challenge."""

    def __init__(self, file_path: Path, file_type: str = "file"):
        self.file_path = file_path
        self.file_type = file_type
        super().__init__(f"The {file_type} '{file_path}' does not exist.")


class InvalidFileTypeError(CTFArchitectError):
    """Raised when a file is not of the expected type."""

    def __init__(self, file_path: Path, expected_type: str = "file"):
        self.file_path = file_path
        self.expected_type = expected_type
        super().__init__(f"The path '{file_path}' is not a {expected_type}.")


class FolderOutsideRepositoryError(CTFArchitectError):
    """Raised when a folder is outside the repository challenges directory."""

    def __init__(self, folder_path: Path):
        self.folder_path = folder_path
        super().__init__(f"The specified folder '{folder_path}' is not in the repository challenges directory.")
