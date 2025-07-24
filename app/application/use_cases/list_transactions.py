from typing import Dict, List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.domain.entities.transaction import Transaction
from app.domain.repositories.transaction_repository import ITransactionRepository
from app.domain.repositories.account_repository import IAccountRepository
from app.core.exceptions import AccountNotFoundException


class ListTransactionsUseCase:
    """Use case for listing transactions with pagination and filtering"""

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        account_repo: IAccountRepository,
    ):
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo

    def execute(
        self,
        db: Session,
        account_id: int,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """Execute list transactions use case with pagination"""

        account = self.account_repo.get_by_id(db, account_id)
        if not account:
            raise AccountNotFoundException("Account not found")

        transactions = self.transaction_repo.list_by_account(
            db, account_id, page, limit, start_date, end_date
        )

        total_count = self.transaction_repo.count_by_account(
            db, account_id, start_date, end_date
        )

        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "account_id": account_id,
            "account_number": account.account_number,
            "transactions": transactions,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            },
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        }
