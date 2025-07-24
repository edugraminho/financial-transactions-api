from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from app.core.enums import TransactionType


class MoneySchema(BaseModel):
    """Schema for Money value object"""

    amount: str = Field(..., description="Amount as string to preserve precision")
    currency: str = Field(default="BRL", min_length=3, max_length=3)

    @validator("amount")
    def validate_amount(cls, v):
        """Validate amount is a valid decimal"""

        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return str(amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")

    class Config:
        schema_extra = {"example": {"amount": "100.50", "currency": "BRL"}}


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""

    account_id: int = Field(..., gt=0, description="Account ID")
    amount: str = Field(..., description="Transaction amount")
    transaction_type: TransactionType = Field(
        ..., description="Transaction type (credit/debit)"
    )
    description: str = Field(
        ..., min_length=1, max_length=500, description="Transaction description"
    )
    transaction_date: Optional[date] = Field(
        None, description="Transaction date (defaults to today)"
    )
    reference_id: Optional[str] = Field(
        None, max_length=255, description="External reference ID"
    )

    @validator("amount")
    def validate_amount(cls, v):
        """Validate amount is positive decimal"""
        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return str(amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")

    @validator("description")
    def validate_description(cls, v):
        """Validate and clean description"""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "amount": "100.50",
                "transaction_type": "credit",
                "description": "Initial deposit",
                "transaction_date": "2024-01-15",
                "reference_id": "REF-001",
            }
        }


class TransactionResponse(BaseModel):
    """Schema for transaction response."""

    id: int
    account_id: int
    amount: MoneySchema
    transaction_type: TransactionType
    description: str
    transaction_date: date
    created_at: datetime
    reference_id: Optional[str] = None

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "account_id": 1,
                "amount": {"amount": "100.50", "currency": "BRL"},
                "transaction_type": "credit",
                "description": "Initial deposit",
                "transaction_date": "2024-01-15",
                "created_at": "2024-01-15T10:00:00Z",
                "reference_id": "REF-001",
            }
        }


class TransactionListResponse(BaseModel):
    """Schema for transaction list response with pagination."""

    account_id: int
    account_number: str
    transactions: List[TransactionResponse]
    pagination: dict
    filters: dict

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "account_number": "ACC-001",
                "transactions": [
                    {
                        "id": 1,
                        "account_id": 1,
                        "amount": {"amount": "100.50", "currency": "BRL"},
                        "transaction_type": "credit",
                        "description": "Initial deposit",
                        "transaction_date": "2024-01-15",
                        "created_at": "2024-01-15T10:00:00Z",
                        "reference_id": "REF-001",
                    }
                ],
                "pagination": {"page": 1, "limit": 50, "total": 1},
                "filters": {"start_date": None, "end_date": None},
            }
        }
