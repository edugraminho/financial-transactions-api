
class FinancialException(Exception):
    """Base exception for financial operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AccountNotFoundException(FinancialException):
    """Raised when account is not found."""

    pass


class InvalidTransactionException(FinancialException):
    """Raised when transaction data is invalid."""

    pass


class InsufficientFundsException(FinancialException):
    """Raised when account has insufficient balance."""

    pass
