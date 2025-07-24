from enum import Enum as PyEnum


class TransactionType(str, PyEnum):
    """Transaction types for financial operations."""

    CREDIT = "credit"
    DEBIT = "debit"


class AccountStatus(str, PyEnum):
    """Account status for financial accounts."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
