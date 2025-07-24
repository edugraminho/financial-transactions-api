from sqlalchemy.orm import Session
from app.domain.entities.transaction import Transaction
from app.domain.entities.account import Account
from app.domain.repositories.transaction_repository import ITransactionRepository
from app.domain.repositories.account_repository import IAccountRepository
from app.application.services.cache_service import CacheService
from app.core.exceptions import AccountNotFoundException, InvalidTransactionException


class CreateTransactionUseCase:
    """Use case for creating financial transactions"""

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        account_repo: IAccountRepository,
        cache_service: CacheService,
    ):
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo
        self.cache_service = cache_service

    def execute(self, db: Session, transaction_data: dict) -> Transaction:
        """Execute the create transaction use case"""

        account = self.account_repo.get_by_id(db, transaction_data["account_id"])
        if not account:
            raise AccountNotFoundException("Account not found")

        account.validate_for_transaction()

        if transaction_data["transaction_type"] == "credit":
            transaction = Transaction.create_credit(
                account_id=transaction_data["account_id"],
                amount=transaction_data["amount"],
                description=transaction_data["description"],
                transaction_date=transaction_data.get("transaction_date"),
                reference_id=transaction_data.get("reference_id"),
            )
        else:
            transaction = Transaction.create_debit(
                account_id=transaction_data["account_id"],
                amount=transaction_data["amount"],
                description=transaction_data["description"],
                transaction_date=transaction_data.get("transaction_date"),
                reference_id=transaction_data.get("reference_id"),
            )

        created_transaction = self.transaction_repo.create_no_commit(db, transaction)

        self.cache_service.invalidate_account(transaction_data["account_id"])

        return created_transaction
