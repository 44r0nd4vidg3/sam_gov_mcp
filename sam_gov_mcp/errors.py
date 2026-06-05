"""Custom exceptions for SAM.gov MCP Server."""


class SamMcpException(Exception):
    """Base exception for SAM.gov MCP Server."""

    pass


class InvalidConfigurationError(SamMcpException):
    """Raised when configuration is invalid."""

    pass


class APIError(SamMcpException):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass


class BadRequestError(APIError):
    """Raised for 400 Bad Request responses."""

    pass


class NotFoundError(APIError):
    """Raised for 404 Not Found responses."""

    pass


class ServerError(APIError):
    """Raised for 500+ server errors."""

    pass


class ValidationError(SamMcpException):
    """Raised when validation fails."""

    pass


class CacheError(SamMcpException):
    """Raised when cache operations fail."""

    pass