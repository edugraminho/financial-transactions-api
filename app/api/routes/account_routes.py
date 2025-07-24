from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DatabaseDep
from app.api.schemas.account_schemas import (
    AccountCreate,
    AccountResponse,
    AccountListResponse,
)
from app.infrastructure.repositories.account_repository import (
    AccountRepository,
)
from app.domain.entities.account import Account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: DatabaseDep,
):
    """Create new financial account"""

    try:
        account_repo = AccountRepository()

        if account_repo.exists_by_account_number(db, account_data.account_number):
            raise HTTPException(
                status_code=422,
                detail=f"Account number '{account_data.account_number}' already exists",
            )

        new_account = Account.create(
            account_number=account_data.account_number,
            account_name=account_data.account_name,
        )

        created_account = account_repo.create_no_commit(db, new_account)

        return _domain_to_response(created_account)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    db: DatabaseDep,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List all accounts with pagination"""

    try:
        account_repo = AccountRepository()

        accounts = account_repo.list_all(db, page, limit)

        account_responses = [_domain_to_response(account) for account in accounts]

        return AccountListResponse(
            accounts=account_responses, total_count=len(account_responses)
        )

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


def _domain_to_response(domain_account: Account) -> AccountResponse:
    """Convert domain Account to response schema"""

    return AccountResponse(
        id=domain_account.id,
        account_number=domain_account.account_number,
        account_name=domain_account.account_name,
        status=domain_account.status,
        created_at=domain_account.created_at,
        updated_at=domain_account.updated_at,
    )
