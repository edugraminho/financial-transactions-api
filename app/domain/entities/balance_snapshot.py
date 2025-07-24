from dataclasses import dataclass
from datetime import datetime, date, timezone
from decimal import Decimal


@dataclass
class BalanceSnapshot:
    """Domain entity representing a balance snapshot."""

    id: int
    account_id: int
    snapshot_date: date
    balance_amount: Decimal
    created_at: datetime
    transaction_count: int = 0
    snapshot_type: str = "daily"

    @classmethod
    def create(
        cls,
        account_id: int,
        snapshot_date: date,
        balance_amount: Decimal,
        transaction_count: int = 0,
        snapshot_type: str = "daily",
    ) -> "BalanceSnapshot":
        """Factory method to create new balance snapshot."""

        return cls(
            id=0,
            account_id=account_id,
            snapshot_date=snapshot_date,
            balance_amount=balance_amount,
            created_at=datetime.now(timezone.utc),
            transaction_count=transaction_count,
            snapshot_type=snapshot_type,
        )
