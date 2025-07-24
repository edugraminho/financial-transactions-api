from decimal import Decimal
from dataclasses import dataclass
from app.core.exceptions import InvalidTransactionException


@dataclass(frozen=True)
class Money:
    """Value object for monetary values with proper decimal handling"""

    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self):
        """Validate money object after initialization"""

        # Convert to Decimal first if needed
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        if self.amount < 0:
            raise InvalidTransactionException("Money amount cannot be negative")

    def add(self, other: "Money") -> "Money":
        """Add two money objects safely."""

        self._validate_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        """Subtract two money objects safely."""

        self._validate_currency(other)
        result_amount = self.amount - other.amount
        return Money(result_amount, self.currency)

    def _validate_currency(self, other: "Money"):
        """Validate that currencies match for operations."""

        if self.currency != other.currency:
            raise InvalidTransactionException(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""

        return {"amount": str(self.amount), "currency": self.currency}

    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str = "BRL") -> "Money":
        """Create Money from Decimal amount."""

        return cls(amount, currency)

    @classmethod
    def zero(cls, currency: str = "BRL") -> "Money":
        """Create zero money object."""

        return cls(Decimal("0.00"), currency)
