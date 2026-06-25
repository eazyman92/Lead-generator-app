class AppError(Exception):
    """Base application error rendered through the standard API contract."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class AuthenticationError(AppError):
    """Authentication failed or is required."""

    def __init__(
        self,
        code: str = "AUTHENTICATION_REQUIRED",
        message: str = "Authentication required.",
    ) -> None:
        super().__init__(401, code, message)


class AuthorizationError(AppError):
    """Authenticated user does not have required permission."""

    def __init__(
        self,
        code: str = "PERMISSION_DENIED",
        message: str = "Permission denied.",
    ) -> None:
        super().__init__(403, code, message)


class CsrfError(AppError):
    """CSRF validation failed."""

    def __init__(self, failure_reason: str = "csrf_validation_failed") -> None:
        self.failure_reason = failure_reason
        super().__init__(403, "CSRF_VALIDATION_FAILED", "CSRF validation failed.")


class ConflictError(AppError):
    """Requested operation conflicts with existing state."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(409, code, message)


class NotFoundError(AppError):
    """Requested resource was not found."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(404, code, message)


class RateLimitError(AppError):
    """Request exceeded an application rate limit."""

    def __init__(
        self,
        code: str = "RATE_LIMIT_EXCEEDED",
        message: str = "Rate limit exceeded.",
    ) -> None:
        super().__init__(429, code, message)


class ValidationAppError(AppError):
    """Application-level validation failed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(422, code, message)
