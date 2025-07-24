from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.domain.entities.transaction import Transaction
from app.domain.repositories.transaction_repository import ITransactionRepository
from app.models.models import TransactionModel
from app.core.enums import TransactionType
from app.domain.value_objects.money import Money


class TransactionRepository(ITransactionRepository):
    """SQLAlchemy Transaction repository."""

    def create_no_commit(self, db: Session, transaction: Transaction) -> Transaction:
        """Create transaction without committing."""

        db_transaction = TransactionModel(
            account_id=transaction.account_id,
            amount=transaction.amount.amount,
            transaction_type=transaction.transaction_type,
            description=transaction.description,
            transaction_date=transaction.transaction_date,
            created_at=transaction.created_at,
            reference_id=transaction.reference_id,
        )

        db.add(db_transaction)
        db.flush()

        transaction.id = db_transaction.id
        return transaction

    def get_by_id(self, db: Session, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""

        db_transaction = (
            db.query(TransactionModel)
            .filter(TransactionModel.id == transaction_id)
            .first()
        )

        if not db_transaction:
            return None

        return self._to_domain_entity(db_transaction)

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

        offset = (page - 1) * limit
        query = db.query(TransactionModel).filter(
            TransactionModel.account_id == account_id
        )

        if start_date:
            query = query.filter(TransactionModel.transaction_date >= start_date)

        if end_date:
            query = query.filter(TransactionModel.transaction_date <= end_date)

        db_transactions = (
            query.order_by(TransactionModel.transaction_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [self._to_domain_entity(tx) for tx in db_transactions]

    def get_balance_by_date(
        self, db: Session, account_id: int, target_date: date
    ) -> Decimal:
        """Calculate account balance up to a specific date."""

        result = (
            db.query(
                func.sum(
                    case(
                        (
                            TransactionModel.transaction_type == TransactionType.CREDIT,
                            TransactionModel.amount,
                        ),
                        else_=-TransactionModel.amount,
                    )
                )
            )
            .filter(
                TransactionModel.account_id == account_id,
                TransactionModel.transaction_date <= target_date,
            )
            .scalar()
        )

        return result or Decimal("0.00")

    def count_by_account(
        self,
        db: Session,
        account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Count transactions for an account with date filters."""

        query = db.query(TransactionModel).filter(
            TransactionModel.account_id == account_id
        )

        if start_date:
            query = query.filter(TransactionModel.transaction_date >= start_date)

        if end_date:
            query = query.filter(TransactionModel.transaction_date <= end_date)

        return query.count()

    def _to_domain_entity(self, db_transaction: TransactionModel) -> Transaction:
        """Convert SQLAlchemy model to domain entity."""

        return Transaction(
            id=db_transaction.id,
            account_id=db_transaction.account_id,
            amount=Money(db_transaction.amount),
            transaction_type=db_transaction.transaction_type,
            description=db_transaction.description,
            transaction_date=db_transaction.transaction_date,
            created_at=db_transaction.created_at,
            reference_id=db_transaction.reference_id,
        )
