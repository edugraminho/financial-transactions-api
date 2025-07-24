"""
Unit tests for Transaction entity.

Tests the Transaction domain entity to verify business rules,
validation logic, and proper instantiation with factory methods.
"""

import pytest
import time
from datetime import datetime, date, timezone
from decimal import Decimal
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.core.enums import TransactionType
from app.core.exceptions import InvalidTransactionException


class TestTransactionCreation:
    """Test Transaction entity creation and factory methods."""

    def test_create_credit_transaction_with_factory(self):
        """Should create credit transaction using factory method"""

        amount = Money("100.50", "BRL")
        transaction = Transaction.create_credit(
            account_id=1,
            amount=amount,
            description="Salary deposit",
            reference_id="SAL-001",
        )

        assert transaction.account_id == 1
        assert transaction.amount == amount
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.description == "Salary deposit"
        assert transaction.transaction_date == date.today()
        assert transaction.reference_id == "SAL-001"
        assert transaction.id == 0
        assert isinstance(transaction.created_at, datetime)
        assert transaction.created_at.tzinfo == timezone.utc

    def test_create_debit_transaction_with_factory(self):
        """Should create debit transaction using factory method."""

        amount = Money("50.25", "BRL")
        transaction = Transaction.create_debit(
            account_id=2,
            amount=amount,
            description="Purchase at supermarket",
            reference_id="PUR-001",
        )

        assert transaction.account_id == 2
        assert transaction.amount == amount
        assert transaction.transaction_type == TransactionType.DEBIT
        assert transaction.description == "Purchase at supermarket"
        assert transaction.transaction_date == date.today()
        assert transaction.reference_id == "PUR-001"

    def test_create_transaction_with_specific_date(self):
        """Should create transaction with specific date."""

        amount = Money("200.00", "BRL")
        specific_date = date(2024, 1, 15)

        transaction = Transaction.create_credit(
            account_id=1,
            amount=amount,
            description="Transfer",
            transaction_date=specific_date,
        )

        assert transaction.transaction_date == specific_date

    def test_create_transaction_without_reference_id(self):
        """Should create transaction without reference ID."""

        amount = Money("75.00", "BRL")

        transaction = Transaction.create_debit(
            account_id=1, amount=amount, description="Cash withdrawal"
        )

        assert transaction.reference_id is None

    def test_create_transaction_strips_description(self):
        """Should strip whitespace from description."""

        amount = Money("100.00", "BRL")

        transaction = Transaction.create_credit(
            account_id=1, amount=amount, description="  Deposit with spaces  "
        )

        assert transaction.description == "Deposit with spaces"

    def test_direct_instantiation_triggers_validation(self):
        """Should trigger validation when directly instantiating Transaction."""

        amount = Money("100.00", "BRL")

        transaction = Transaction(
            id=1,
            account_id=1,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description="Valid transaction",
            transaction_date=date.today(),
            created_at=datetime.now(timezone.utc),
        )

        assert transaction.description == "Valid transaction"


class TestTransactionValidation:
    """Test Transaction validation rules"""

    def test_zero_amount_raises_error(self):
        """Should raise InvalidTransactionException for zero amount"""
        with pytest.raises(
            InvalidTransactionException, match="Transaction amount must be positive"
        ):
            Transaction.create_credit(
                account_id=1,
                amount=Money("0.00", "BRL"),
                description="Zero amount transaction",
            )

    def test_negative_amount_raises_error(self):
        """Should raise InvalidTransactionException for negative amount in Money"""
        with pytest.raises(
            InvalidTransactionException, match="Money amount cannot be negative"
        ):
            Money("-100.00", "BRL")

    def test_empty_description_raises_error(self):
        """Should raise InvalidTransactionException for empty description"""

        with pytest.raises(
            InvalidTransactionException, match="Transaction description is required"
        ):
            Transaction.create_debit(
                account_id=1, amount=Money("100.00", "BRL"), description=""
            )

    def test_whitespace_only_description_raises_error(self):
        """Should raise InvalidTransactionException for whitespace-only description."""
        with pytest.raises(
            InvalidTransactionException, match="Transaction description is required"
        ):
            Transaction.create_credit(
                account_id=1, amount=Money("100.00", "BRL"), description="   "
            )

    def test_too_long_description_raises_error(self):
        """Should raise InvalidTransactionException for description longer than 500 characters."""
        long_description = "A" * 501

        with pytest.raises(
            InvalidTransactionException, match="Transaction description too long"
        ):
            Transaction.create_debit(
                account_id=1,
                amount=Money("100.00", "BRL"),
                description=long_description,
            )

    def test_exactly_500_character_description_is_valid(self):
        """Should accept description with exactly 500 characters."""
        description_500 = "A" * 500
        amount = Money("100.00", "BRL")

        transaction = Transaction.create_credit(
            account_id=1, amount=amount, description=description_500
        )

        assert len(transaction.description) == 500


class TestTransactionTypeChecking:
    """Test Transaction type checking methods."""

    def test_is_credit_for_credit_transaction(self):
        """Should return True for credit transactions."""
        transaction = Transaction.create_credit(
            account_id=1,
            amount=Money("100.00", "BRL"),
            description="Credit transaction",
        )

        assert transaction.is_credit() is True
        assert transaction.is_debit() is False

    def test_is_debit_for_debit_transaction(self):
        """Should return True for debit transactions."""
        transaction = Transaction.create_debit(
            account_id=1, amount=Money("100.00", "BRL"), description="Debit transaction"
        )

        assert transaction.is_debit() is True
        assert transaction.is_credit() is False


class TestTransactionSerialization:
    """Test Transaction serialization methods."""

    def test_to_dict_credit_transaction(self):
        """Should convert credit transaction to dictionary correctly."""
        amount = Money("250.75", "BRL")
        transaction_date = date(2024, 1, 15)
        created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        transaction = Transaction(
            id=123,
            account_id=1,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description="Test credit",
            transaction_date=transaction_date,
            created_at=created_at,
            reference_id="REF-001",
        )

        result = transaction.to_dict()

        expected = {
            "id": 123,
            "account_id": 1,
            "amount": {"amount": "250.75", "currency": "BRL"},
            "transaction_type": "credit",
            "description": "Test credit",
            "transaction_date": "2024-01-15",
            "created_at": "2024-01-15T10:30:00+00:00",
            "reference_id": "REF-001",
        }

        assert result == expected

    def test_to_dict_debit_transaction_without_reference(self):
        """Should convert debit transaction without reference to dictionary correctly."""
        amount = Money("100.00", "EUR")
        transaction_date = date(2024, 2, 1)
        created_at = datetime(2024, 2, 1, 14, 45, 30, tzinfo=timezone.utc)

        transaction = Transaction(
            id=456,
            account_id=2,
            amount=amount,
            transaction_type=TransactionType.DEBIT,
            description="Test debit",
            transaction_date=transaction_date,
            created_at=created_at,
            reference_id=None,
        )

        result = transaction.to_dict()

        expected = {
            "id": 456,
            "account_id": 2,
            "amount": {"amount": "100.00", "currency": "EUR"},
            "transaction_type": "debit",
            "description": "Test debit",
            "transaction_date": "2024-02-01",
            "created_at": "2024-02-01T14:45:30+00:00",
            "reference_id": None,
        }

        assert result == expected


class TestTransactionEdgeCases:
    """Test Transaction edge cases and boundary conditions."""

    def test_transaction_with_very_large_amount(self):
        """Should handle transactions with very large amounts."""
        large_amount = Money("999999999.99", "BRL")

        transaction = Transaction.create_credit(
            account_id=1, amount=large_amount, description="Large amount transaction"
        )

        assert transaction.amount.amount == Decimal("999999999.99")

    def test_transaction_with_very_small_amount(self):
        """Should handle transactions with very small amounts."""
        small_amount = Money("0.01", "BRL")

        transaction = Transaction.create_debit(
            account_id=1, amount=small_amount, description="Small amount transaction"
        )

        assert transaction.amount.amount == Decimal("0.01")

    def test_transaction_timestamp_precision(self):
        """Should maintain timestamp precision for created_at."""
        transaction1 = Transaction.create_credit(
            account_id=1, amount=Money("100.00", "BRL"), description="First transaction"
        )

        time.sleep(0.001)  # Small delay

        transaction2 = Transaction.create_credit(
            account_id=1, amount=Money("200.00", "BRL"), description="Second transaction"
        )

        assert transaction2.created_at > transaction1.created_at


class TestTransactionEquality:
    """Test Transaction equality and comparison operations."""

    def test_transaction_equality_with_same_data(self):
        """Should be equal when all data is the same."""
        amount = Money("100.00", "BRL")
        transaction_date = date(2024, 1, 15)
        created_at = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        transaction1 = Transaction(
            id=1,
            account_id=1,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description="Same transaction",
            transaction_date=transaction_date,
            created_at=created_at,
            reference_id="REF-001",
        )

        transaction2 = Transaction(
            id=1,
            account_id=1,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description="Same transaction",
            transaction_date=transaction_date,
            created_at=created_at,
            reference_id="REF-001",
        )

        assert transaction1 == transaction2
