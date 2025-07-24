from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, validator
from app.core.enums import AccountStatus


class AccountCreate(BaseModel):
    """Schema for creating an account"""

    account_number: str = Field(
        ..., min_length=1, max_length=50, description="Unique account number"
    )
    account_name: str = Field(
        ..., min_length=1, max_length=255, description="Account display name"
    )

    @validator("account_number")
    def validate_account_number(cls, v):
        """Validate and clean account number."""
        if not v or not v.strip():
            raise ValueError("Account number cannot be empty")
        return v.strip()

    @validator("account_name")
    def validate_account_name(cls, v):
        """Validate and clean account name"""
        if not v or not v.strip():
            raise ValueError("Account name cannot be empty")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "account_number": "ACC-001",
                "account_name": "Main Business Account",
            }
        }


class AccountResponse(BaseModel):
    """Schema for account response."""

    id: int
    account_number: str
    account_name: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "account_number": "ACC-001",
                "account_name": "Main Business Account",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }


class AccountListResponse(BaseModel):
    """Schema for account list response."""

    accounts: List[AccountResponse]
    total_count: int

    class Config:
        schema_extra = {
            "example": {
                "accounts": [
                    {
                        "id": 1,
                        "account_number": "ACC-001",
                        "account_name": "Main Business Account",
                        "status": "active",
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T10:00:00Z",
                    }
                ],
                "total_count": 1,
            }
        }
