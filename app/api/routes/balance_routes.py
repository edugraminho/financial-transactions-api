from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import DatabaseDep
from app.api.schemas.balance_schemas import BalanceResponse
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.services.cache_service import CacheService
from app.infrastructure.repositories.account_repository import (
    AccountRepository,
)
from app.infrastructure.repositories.transaction_repository import (
    TransactionRepository,
)
from app.infrastructure.repositories.balance_snapshot_repository import (
    BalanceSnapshotRepository,
)
from app.infrastructure.services.redis_cache_service import RedisCacheService
from app.domain.services.balance_calculator import BalanceCalculatorService
from app.application.services.snapshot_service import SnapshotService
from app.core.exceptions import AccountNotFoundException

router = APIRouter(prefix="/accounts", tags=["balance"])


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_account_balance(
    account_id: int,
    db: DatabaseDep,
    target_date: Optional[date] = Query(None, description="Balance date (defaults to today)"),
):
    """Get account balance at specific date with cache strategy."""

    try:
        use_case = _create_get_balance_use_case()

        result = use_case.execute(
            db=db, account_id=account_id, target_date=target_date
        )

        # Transform use case result to match BalanceResponse schema
        response_data = {
            "account_id": result["account"]["id"],
            "account_number": result["account"]["account_number"],
            "account_name": result["account"]["account_name"],
            "balance": result["balance"],
            "date": result["target_date"],
            "source": result["source"],
        }

        return response_data

    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


def _create_get_balance_use_case() -> GetBalanceUseCase:
    """Factory function to create get balance use case with dependencies"""

    account_repo = AccountRepository()
    transaction_repo = TransactionRepository()
    snapshot_repo = BalanceSnapshotRepository()
    balance_calculator = BalanceCalculatorService()
    cache_service = CacheService(RedisCacheService())
    snapshot_service = SnapshotService(snapshot_repo, transaction_repo)

    return GetBalanceUseCase(
        account_repo, transaction_repo, snapshot_repo, balance_calculator, cache_service, snapshot_service
    )
