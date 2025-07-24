from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.account import Account
from app.domain.repositories.account_repository import IAccountRepository
from app.models.models import AccountModel
from app.core.enums import AccountStatus
from datetime import datetime, timezone


class AccountRepository(IAccountRepository):
    """SQLAlchemy Account repository."""

    def create_no_commit(self, db: Session, account: Account) -> Account:
        """Create account without committing transaction"""

        db_account = AccountModel(
            account_number=account.account_number,
            account_name=account.account_name,
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

        db.add(db_account)
        db.flush()

        account.id = db_account.id
        return account

    def get_by_id(self, db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID."""

        db_account = (
            db.query(AccountModel).filter(AccountModel.id == account_id).first()
        )

        if not db_account:
            return None

        return self._to_domain_entity(db_account)

    def get_by_account_number(
        self, db: Session, account_number: str
    ) -> Optional[Account]:
        """Get account by account number."""
        db_account = (
            db.query(AccountModel)
            .filter(AccountModel.account_number == account_number)
            .first()
        )

        if not db_account:
            return None

        return self._to_domain_entity(db_account)

    def list_all(self, db: Session, page: int = 1, limit: int = 50) -> List[Account]:
        """List all accounts with pagination."""
        offset = (page - 1) * limit

        db_accounts = db.query(AccountModel).offset(offset).limit(limit).all()

        return [self._to_domain_entity(db_account) for db_account in db_accounts]

    def update_no_commit(self, db: Session, account: Account) -> Account:
        """Update account without committing transaction."""
        db.query(AccountModel).filter(AccountModel.id == account.id).update(
            {
                AccountModel.account_name: account.account_name,
                AccountModel.status: account.status,
                AccountModel.updated_at: datetime.now(timezone.utc),
            }
        )

        db.flush()
        return account

    def exists_by_account_number(self, db: Session, account_number: str) -> bool:
        """Check if account number exists."""

        count = (
            db.query(AccountModel)
            .filter(AccountModel.account_number == account_number)
            .count()
        )

        return count > 0

    def _to_domain_entity(self, db_account: AccountModel) -> Account:
        """Convert SQLAlchemy model to domain entity"""

        created_at = db_account.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        updated_at = db_account.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        return Account(
            id=db_account.id,
            account_number=db_account.account_number,
            account_name=db_account.account_name,
            status=db_account.status,
            created_at=created_at,
            updated_at=updated_at,
        )
