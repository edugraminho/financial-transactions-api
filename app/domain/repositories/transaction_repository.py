from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.domain.entities.transaction import Transaction


class ITransactionRepository(ABC):
    """Transaction repository interface defining contract for data access"""

    @abstractmethod
    def create_no_commit(self, db: Session, transaction: Transaction) -> Transaction:
        """Create transaction without committing."""
        pass

    @abstractmethod
    def get_by_id(self, db: Session, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        pass

    @abstractmethod
    def list_by_account(
        self,
        db: Session,
        account_id: int,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Transaction]:
        """List transactions by account with pagination and date filters."""
        pass

    @abstractmethod
    def get_balance_by_date(
        self, db: Session, account_id: int, target_date: date
    ) -> Decimal:
        """Calculate account balance up to a specific date."""
        pass

    @abstractmethod
    def count_by_account(
        self,
        db: Session,
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Count transactions for an account with date filters."""
        pass
