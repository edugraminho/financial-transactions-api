from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.domain.entities.account import Account
from app.domain.repositories.transaction_repository import ITransactionRepository
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.balance_snapshot_repository import (
    IBalanceSnapshotRepository,
)
from app.domain.services.balance_calculator import BalanceCalculatorService
from app.application.services.cache_service import CacheService
from app.application.services.snapshot_service import SnapshotService
from app.domain.value_objects.money import Money
from app.core.exceptions import AccountNotFoundException


class GetBalanceUseCase:
    """Use case for getting account balance with cache-aside strategy."""

    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
        snapshot_repo: IBalanceSnapshotRepository,
        balance_calculator: BalanceCalculatorService,
        cache_service: CacheService,
        snapshot_service: SnapshotService,
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.snapshot_repo = snapshot_repo
        self.balance_calculator = balance_calculator
        self.cache_service = cache_service
        self.snapshot_service = snapshot_service

    def execute(self, db: Session, account_id: int, target_date: date = None) -> dict:
        """
        Execute get balance use case with cache-aside pattern.
            1. Validate account exists
            2. Try cache first (cache-aside)
            3. Cache miss - calculate from database
            4. Cache the calculated result
        """

        if target_date is None:
            target_date = date.today()

        account = self.account_repo.get_by_id(db, account_id)
        if not account:
            raise AccountNotFoundException("Account not found")

        # 1. Try cache first
        cached_balance = self.cache_service.get_cached_balance(account_id, target_date)
        if cached_balance is not None:
            return self._build_response(account, cached_balance, target_date, "cache")

        # 2. Try snapshot
        snapshot = self.snapshot_repo.get_latest_before_date(
            db, account_id, target_date
        )
        if snapshot:
            calculated_balance = self._calculate_from_snapshot(
                db, snapshot, account_id, target_date
            )
            source = "snapshot"
        else:
            # 3. Fallback to full calculation
            balance_amount = self.transaction_repo.get_balance_by_date(
                db, account_id, target_date
            )
            calculated_balance = Money(balance_amount)
            source = "calculated"

            # 4. Auto create snapshot if necessary
            try:
                if self.snapshot_service.should_create_snapshot(db, account_id, target_date):
                    self.snapshot_service.create_daily_snapshot(db, account_id, target_date)
                    source = "calculated+snapshot_created"
            except Exception:
                # Don't fail if snapshot creation fails
                pass

        # Cache the result
        self.cache_service.cache_balance(account_id, target_date, calculated_balance)

        return self._build_response(account, calculated_balance, target_date, source)

    def _calculate_from_snapshot(
        self, db: Session, snapshot, account_id: int, target_date: date
    ) -> Money:
        """Calculate balance from snapshot + subsequent transactions."""

        balance = Money(snapshot.balance_amount)

        # Add transactions after snapshot date
        if snapshot.snapshot_date < target_date:
            transactions = self.transaction_repo.list_by_account(
                db,
                account_id,
                page=1,
                limit=10000,
                start_date=snapshot.snapshot_date + timedelta(days=1),
                end_date=target_date,
            )

            for transaction in transactions:
                if transaction.is_credit():
                    balance = balance.add(transaction.amount)
                else:
                    balance = balance.subtract(transaction.amount)

        return balance

    def _build_response(self, account, balance, target_date, source) -> dict:
        """Build standard response format."""

        return {
            "account_id": account.id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "balance": balance.to_dict(),
            "date": target_date.isoformat(),
            "source": source,
        }
