from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.domain.entities.balance_snapshot import BalanceSnapshot


class IBalanceSnapshotRepository(ABC):
    """Interface for balance snapshot repository."""

    @abstractmethod
    def get_latest_before_date(
        self, db: Session, account_id: int, target_date: date
    ) -> Optional[BalanceSnapshot]:
        """Get latest snapshot before or on target date."""
        pass

    @abstractmethod
    def create_no_commit(
        self, db: Session, snapshot: BalanceSnapshot
    ) -> BalanceSnapshot:
        """Create snapshot without committing."""
        pass

    @abstractmethod
    def exists(self, db: Session, account_id: int, snapshot_date: date) -> bool:
        """Check if snapshot exists for account and date."""
        pass
