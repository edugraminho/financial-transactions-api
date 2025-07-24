from datetime import date, datetime
from sqlalchemy.orm import Session
from app.domain.entities.balance_snapshot import BalanceSnapshot
from app.domain.repositories.balance_snapshot_repository import (
    IBalanceSnapshotRepository,
)
from app.domain.repositories.transaction_repository import ITransactionRepository


class SnapshotService:
    """Service for managing balance snapshots"""

    def __init__(
        self,
        snapshot_repo: IBalanceSnapshotRepository,
        transaction_repo: ITransactionRepository,
    ):
        self.snapshot_repo = snapshot_repo
        self.transaction_repo = transaction_repo

    def create_daily_snapshot(
        self, db: Session, account_id: int, target_date: date
    ) -> BalanceSnapshot:
        """Create daily snapshot for account."""

        if self.snapshot_repo.exists(db, account_id, target_date):
            raise ValueError(
                f"Snapshot already exists for account {account_id} on {target_date}"
            )

        balance_amount = self.transaction_repo.get_balance_by_date(
            db, account_id, target_date
        )

        transaction_count = self.transaction_repo.count_by_account(
            db, account_id, end_date=target_date
        )

        snapshot = BalanceSnapshot.create(
            account_id=account_id,
            snapshot_date=target_date,
            balance_amount=balance_amount,
            transaction_count=transaction_count,
            snapshot_type="daily",
        )

        return self.snapshot_repo.create_no_commit(db, snapshot)

    def should_create_snapshot(
        self, db: Session, account_id: int, target_date: date
    ) -> bool:
        """
        Check if we should create a snapshot for performance reasons
        Create snapshots for accounts with 100+ transactions
        """
        if target_date > date.today():
            return False

        if self.snapshot_repo.exists(db, account_id, target_date):
            return False

        transaction_count = self.transaction_repo.count_by_account(
            db, account_id, end_date=target_date
        )

        return transaction_count > 100
