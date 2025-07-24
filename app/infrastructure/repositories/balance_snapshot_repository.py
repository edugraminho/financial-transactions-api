from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.domain.entities.balance_snapshot import BalanceSnapshot
from app.domain.repositories.balance_snapshot_repository import (
    IBalanceSnapshotRepository,
)
from app.models.models import BalanceSnapshotModel


class BalanceSnapshotRepository(IBalanceSnapshotRepository):
    """SQLAlchemy balance snapshot repository"""

    def get_latest_before_date(
        self, db: Session, account_id: int, target_date: date
    ) -> Optional[BalanceSnapshot]:
        """Get latest snapshot before or on target date."""

        db_snapshot = (
            db.query(BalanceSnapshotModel)
            .filter(
                and_(
                    BalanceSnapshotModel.account_id == account_id,
                    BalanceSnapshotModel.snapshot_date <= target_date,
                )
            )
            .order_by(desc(BalanceSnapshotModel.snapshot_date))
            .first()
        )

        if not db_snapshot:
            return None

        return self._to_domain_entity(db_snapshot)

    def create_no_commit(
        self, db: Session, snapshot: BalanceSnapshot
    ) -> BalanceSnapshot:
        """Create snapshot without committing."""

        db_snapshot = BalanceSnapshotModel(
            account_id=snapshot.account_id,
            snapshot_date=snapshot.snapshot_date,
            balance_amount=snapshot.balance_amount,
            created_at=snapshot.created_at,
            transaction_count=snapshot.transaction_count,
            snapshot_type=snapshot.snapshot_type,
        )

        db.add(db_snapshot)
        db.flush()

        snapshot.id = db_snapshot.id
        return snapshot

    def exists(self, db: Session, account_id: int, snapshot_date: date) -> bool:
        """Check if snapshot exists for account and date."""

        return (
            db.query(BalanceSnapshotModel)
            .filter(
                and_(
                    BalanceSnapshotModel.account_id == account_id,
                    BalanceSnapshotModel.snapshot_date == snapshot_date,
                )
            )
            .first()
            is not None
        )

    def _to_domain_entity(self, db_snapshot: BalanceSnapshotModel) -> BalanceSnapshot:
        """Convert SQLAlchemy model to domain entity."""

        return BalanceSnapshot(
            id=db_snapshot.id,
            account_id=db_snapshot.account_id,
            snapshot_date=db_snapshot.snapshot_date,
            balance_amount=db_snapshot.balance_amount,
            created_at=db_snapshot.created_at,
            transaction_count=db_snapshot.transaction_count,
            snapshot_type=db_snapshot.snapshot_type,
        )
