class LennyAppException(Exception):
    """Base exception for application errors."""
    pass

class ProviderError(LennyAppException):
    """Raised when an LLM provider fails."""
    pass

class SessionNotFoundError(LennyAppException):
    """Raised when a requested chat session does not exist."""
    pass

class InvalidRequestError(LennyAppException):
    """Raised when an API request is invalid."""
    pass
