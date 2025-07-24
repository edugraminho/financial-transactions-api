"""
Unit tests for Money value object.

Tests the Money value object which handles monetary values with proper decimal
precision and currency validation for financial calculations.
"""

import pytest
from decimal import Decimal
from app.domain.value_objects.money import Money
from app.core.exceptions import InvalidTransactionException


class TestMoneyCreation:
    """Test Money object creation and validation."""

    def test_create_money_with_decimal(self):
        """Should create Money object with Decimal amount successfully."""
        money = Money(Decimal("100.50"), "BRL")

        assert money.amount == Decimal("100.50")
        assert money.currency == "BRL"

    def test_create_money_with_string(self):
        """Should create Money object with string amount and convert to Decimal."""
        money = Money("100.50", "USD")

        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_create_money_with_int(self):
        """Should create Money object with integer amount."""
        money = Money(100, "EUR")

        assert money.amount == Decimal("100")
        assert money.currency == "EUR"

    def test_create_money_with_float(self):
        """Should create Money object with float amount and convert to Decimal."""
        money = Money(100.50, "BRL")

        assert money.amount == Decimal("100.50")
        assert money.currency == "BRL"

    def test_create_money_with_default_currency(self):
        """Should use default BRL currency when not specified."""
        money = Money("50.25")

        assert money.amount == Decimal("50.25")
        assert money.currency == "BRL"

    def test_create_money_zero(self):
        """Should create zero Money object successfully."""
        money = Money("0.00")

        assert money.amount == Decimal("0.00")
        assert money.currency == "BRL"

    def test_create_money_invalid_string_raises_error(self):
        """Should raise error for invalid decimal string."""
        with pytest.raises(Exception):
            Money("invalid_amount")


class TestMoneyOperations:
    """Test Money arithmetic operations."""

    def test_add_same_currency(self):
        """Should add two Money objects with same currency correctly."""
        money1 = Money("100.50", "BRL")
        money2 = Money("50.25", "BRL")

        result = money1.add(money2)

        assert result.amount == Decimal("150.75")
        assert result.currency == "BRL"

    def test_subtract_same_currency(self):
        """Should subtract two Money objects with same currency correctly."""
        money1 = Money("100.50", "BRL")
        money2 = Money("30.25", "BRL")

        result = money1.subtract(money2)

        assert result.amount == Decimal("70.25")
        assert result.currency == "BRL"

    def test_add_different_currencies_raises_error(self):
        """Should raise InvalidTransactionException for different currencies."""
        money1 = Money("100.00", "BRL")
        money2 = Money("50.00", "USD")

        with pytest.raises(
            InvalidTransactionException, match="Currency mismatch: BRL vs USD"
        ):
            money1.add(money2)

    def test_subtract_different_currencies_raises_error(self):
        """Should raise InvalidTransactionException for different currencies."""
        money1 = Money("100.00", "EUR")
        money2 = Money("50.00", "BRL")

        with pytest.raises(
            InvalidTransactionException, match="Currency mismatch: EUR vs BRL"
        ):
            money1.subtract(money2)

    def test_add_zero_money(self):
        """Should add zero money correctly."""
        money = Money("100.00", "BRL")
        zero = Money.zero("BRL")

        result = money.add(zero)

        assert result.amount == Decimal("100.00")
        assert result.currency == "BRL"

    def test_subtract_zero_money(self):
        """Should subtract zero money correctly."""
        money = Money("100.00", "BRL")
        zero = Money.zero("BRL")

        result = money.subtract(zero)

        assert result.amount == Decimal("100.00")
        assert result.currency == "BRL"


class TestMoneyComparison:
    """Test Money comparison operations."""

    def test_money_equality(self):
        """Should compare Money objects for equality correctly."""
        money1 = Money("100.50", "BRL")
        money2 = Money("100.50", "BRL")
        money3 = Money("100.51", "BRL")

        assert money1 == money2
        assert money1 != money3

    def test_money_equality_different_currencies(self):
        """Should not consider Money objects with different currencies equal."""
        money_brl = Money("100.00", "BRL")
        money_usd = Money("100.00", "USD")

        assert money_brl != money_usd
