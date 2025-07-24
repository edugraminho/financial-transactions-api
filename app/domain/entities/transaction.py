from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Optional
from app.domain.value_objects.money import Money
from app.core.enums import TransactionType
from app.core.exceptions import InvalidTransactionException


@dataclass
class Transaction:
    """Transaction domain entity representing a financial transaction."""

    id: int
    account_id: int
    amount: Money
    transaction_type: TransactionType
    description: str
    transaction_date: date
    created_at: datetime
    reference_id: Optional[str] = None

    def __post_init__(self):
        """Validate transaction after initialization."""

        self.validate()

    def validate(self):
        """Validate transaction business rules."""

        if self.amount.amount <= 0:
            raise InvalidTransactionException("Transaction amount must be positive")

        if not self.description or len(self.description.strip()) == 0:
            raise InvalidTransactionException("Transaction description is required")

        if len(self.description) > 500:
            raise InvalidTransactionException("Transaction description too long")

    def is_debit(self) -> bool:
        """Check if transaction is a debit."""

        return self.transaction_type == TransactionType.DEBIT

    def is_credit(self) -> bool:
        """Check if transaction is a credit."""

        return self.transaction_type == TransactionType.CREDIT

    @classmethod
    def create_credit(
        cls,
        account_id: int,
        amount: Money,
        description: str,
        transaction_date: date = None,
        reference_id: str = None,
    ) -> "Transaction":
        """Factory method to create credit transaction."""

        return cls._create_transaction(
            account_id,
            amount,
            TransactionType.CREDIT,
            description,
            transaction_date,
            reference_id,
        )

    @classmethod
    def create_debit(
        cls,
        account_id: int,
        amount: Money,
        description: str,
        transaction_date: date = None,
        reference_id: str = None,
    ) -> "Transaction":
        """Factory method to create debit transaction."""

        return cls._create_transaction(
            account_id,
            amount,
            TransactionType.DEBIT,
            description,
            transaction_date,
            reference_id,
        )

    @classmethod
    def _create_transaction(
        cls,
        account_id: int,
        amount: Money,
        transaction_type: TransactionType,
        description: str,
        transaction_date: date = None,
        reference_id: str = None,
    ) -> "Transaction":
        """Internal factory method."""

        return cls(
            id=0,
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description.strip(),
            transaction_date=transaction_date or date.today(),
            created_at=datetime.now(timezone.utc),
            reference_id=reference_id,
        )

    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""

        return {
            "id": self.id,
            "account_id": self.account_id,
            "amount": self.amount.to_dict(),
            "transaction_type": self.transaction_type.value,
            "description": self.description,
            "transaction_date": self.transaction_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "reference_id": self.reference_id,
        }
