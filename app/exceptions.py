"""Domain exceptions. Services raise these; main.py turns them into HTTP responses."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    """The request is valid but clashes with current state (duplicates, wrong status)."""

    status_code = 409


class BusinessRuleError(DomainError):
    """The request breaks a business rule (inactive plan, overpayment, ...)."""

    status_code = 400


class LedgerImmutableError(RuntimeError):
    """Raised when code tries to update or delete a ledger entry."""
