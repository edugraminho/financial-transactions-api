from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class MoneyBalanceSchema(BaseModel):
    """Schema for Money in balance responses (allows zero amounts)"""

    amount: str = Field(..., description="Amount as string to preserve precision")
    currency: str = Field(default="BRL", min_length=3, max_length=3)

    @validator("amount")
    def validate_amount(cls, v):
        """Validate amount is a valid decimal (allows zero for balances)"""

        try:
            amount = Decimal(v)
            if amount < 0:
                raise ValueError("Amount cannot be negative")
            return str(amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")

    class Config:
        schema_extra = {"example": {"amount": "1250.75", "currency": "BRL"}}


class BalanceResponse(BaseModel):
    """Schema for balance response."""

    account_id: int
    account_number: str
    account_name: str
    balance: MoneyBalanceSchema
    date: date
    source: str  # cache or calculated

    class Config:
        schema_extra = {
            "example": {
                "account_id": 1,
                "account_number": "ACC-001",
                "account_name": "Main Account",
                "balance": {"amount": "1250.75", "currency": "BRL"},
                "date": "2024-01-15",
                "source": "cache",
            }
        }
