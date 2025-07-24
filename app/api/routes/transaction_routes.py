from datetime import date
from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.api.schemas.transaction_schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    MoneySchema,
)
from app.application.use_cases.create_transaction import CreateTransactionUseCase
from app.application.use_cases.list_transactions import ListTransactionsUseCase
from app.application.services.cache_service import CacheService
from app.infrastructure.repositories.transaction_repository import (
    TransactionRepository,
)
from app.infrastructure.repositories.account_repository import (
    AccountRepository,
)
from app.infrastructure.services.redis_cache_service import RedisCacheService
from app.domain.value_objects.money import Money
from app.core.exceptions import AccountNotFoundException, InvalidTransactionException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: DatabaseDep,
):
    """Criar nova transação financeira"""

    try:
        use_case = _create_transaction_use_case()

        transaction_dict = {
            "account_id": transaction_data.account_id,
            "amount": Money(transaction_data.amount),
            "transaction_type": transaction_data.transaction_type.value,
            "description": transaction_data.description,
            "transaction_date": transaction_data.transaction_date,
            "reference_id": transaction_data.reference_id,
        }

        domain_transaction = use_case.execute(db, transaction_dict)
        return _domain_to_response(domain_transaction)

    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTransactionException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    db: DatabaseDep,
    account_id: int = Query(..., description="Account ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
):
    """Listar transações de uma conta com paginação e filtros"""

    try:
        use_case = _create_list_transactions_use_case()

        result = use_case.execute(
            db=db,
            account_id=account_id,
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        transaction_responses = [
            _domain_to_response(domain_transaction)
            for domain_transaction in result["transactions"]
        ]

        return TransactionListResponse(
            account_id=result["account_id"],
            account_number=result["account_number"],
            transactions=transaction_responses,
            pagination=result["pagination"],
            filters=result["filters"],
        )

    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


def _create_transaction_use_case() -> CreateTransactionUseCase:
    """Factory function to create transaction use case with dependencies"""

    transaction_repo = TransactionRepository()
    account_repo = AccountRepository()
    cache_service = CacheService(RedisCacheService())

    return CreateTransactionUseCase(transaction_repo, account_repo, cache_service)


def _create_list_transactions_use_case() -> ListTransactionsUseCase:
    """Factory function to create list transactions use case with dependencies"""

    transaction_repo = TransactionRepository()
    account_repo = AccountRepository()

    return ListTransactionsUseCase(transaction_repo, account_repo)


def _domain_to_response(domain_transaction) -> TransactionResponse:
    """Convert domain Transaction to response schema"""

    return TransactionResponse(
        id=domain_transaction.id,
        account_id=domain_transaction.account_id,
        amount=MoneySchema(
            amount=str(domain_transaction.amount.amount),
            currency=domain_transaction.amount.currency,
        ),
        transaction_type=domain_transaction.transaction_type,
        description=domain_transaction.description,
        transaction_date=domain_transaction.transaction_date,
        created_at=domain_transaction.created_at,
        reference_id=domain_transaction.reference_id,
    )
