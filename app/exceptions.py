"""Application-specific exceptions and API error mapping."""

from __future__ import annotations


class AppError(Exception):
    """Base class for structured API errors."""

    status_code = 400
    code = "app_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidFileError(AppError):
    """Raised when an upload is empty or otherwise invalid."""

    status_code = 400
    code = "invalid_file"


class UploadTooLargeError(AppError):
    """Raised when an upload exceeds the configured size limit."""

    status_code = 413
    code = "upload_too_large"


class UnsupportedFormatError(AppError):
    """Raised when a file extension or geospatial format is unsupported."""

    status_code = 415
    code = "unsupported_format"


class UnreadableFileError(AppError):
    """Raised when a supported file cannot be parsed."""

    status_code = 422
    code = "unreadable_file"


class ProcessingConflictError(AppError):
    """Raised when measurements are requested before processing completed."""

    status_code = 409
    code = "file_not_completed"

