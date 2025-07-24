from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.enums import AccountStatus
from app.core.exceptions import AccountNotFoundException


@dataclass
class Account:
    """Account domain entity representing a financial account."""

    id: int
    account_number: str
    account_name: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime

    def activate(self):
        """Activate the account"""

        self.status = AccountStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate the account."""

        self.status = AccountStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def block(self):
        """Block the account."""

        self.status = AccountStatus.BLOCKED
        self.updated_at = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if account is active and can perform transactions."""

        return self.status == AccountStatus.ACTIVE

    def validate_for_transaction(self):
        """Validate account can perform transactions."""

        if not self.is_active():
            raise AccountNotFoundException(
                f"Account {self.account_number} is not active"
            )

    @classmethod
    def create(cls, account_number: str, account_name: str) -> "Account":
        """Factory method to create new account."""

        now = datetime.now(timezone.utc)
        return cls(
            id=0,
            account_number=account_number,
            account_name=account_name,
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        """Convert account to dictionary."""

        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_name": self.account_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
