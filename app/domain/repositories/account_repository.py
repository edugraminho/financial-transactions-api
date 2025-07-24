from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.account import Account


class IAccountRepository(ABC):
    """Account repository interface defining contract for data access"""

    @abstractmethod
    def create_no_commit(self, db: Session, account: Account) -> Account:
        """Create account without committing transaction"""
        pass

    @abstractmethod
    def get_by_id(self, db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID."""
        pass

    @abstractmethod
    def get_by_account_number(
        self, db: Session, account_number: str
    ) -> Optional[Account]:
        """Get account by account number."""
        pass

    @abstractmethod
    def list_all(self, db: Session, page: int = 1, limit: int = 50) -> List[Account]:
        """List all accounts with pagination."""
        pass

    @abstractmethod
    def update_no_commit(self, db: Session, account: Account) -> Account:
        """Update account without committing transaction."""
        pass

    @abstractmethod
    def exists_by_account_number(self, db: Session, account_number: str) -> bool:
        """Check if account number exists."""
        pass
