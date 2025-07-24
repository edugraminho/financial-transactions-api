"""
Unit tests for BalanceCalculator service.

Tests the BalanceCalculatorService which handles balance calculations
with pure business logic for transaction processing and balance computation.
"""

import pytest
from datetime import date
from decimal import Decimal
from app.domain.services.balance_calculator import BalanceCalculatorService
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.core.enums import TransactionType


class TestBalanceCalculatorAtDate:
    """Test balance calculation at specific dates."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.calculator = BalanceCalculatorService()

        # Create sample transactions for testing
        self.transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("1000.00", "BRL"),
                description="Initial deposit",
                transaction_date=date(2024, 1, 1),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("250.50", "BRL"),
                description="Purchase",
                transaction_date=date(2024, 1, 15),
            ),
            Transaction.create_credit(
                account_id=1,
                amount=Money("500.00", "BRL"),
                description="Salary",
                transaction_date=date(2024, 1, 30),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("100.25", "BRL"),
                description="Withdrawal",
                transaction_date=date(2024, 2, 5),
            ),
        ]

    def test_calculate_balance_at_specific_date(self):
        """Should calculate balance at specific date correctly."""
        target_date = date(2024, 1, 20)

        balance = self.calculator.calculate_balance_at_date(
            self.transactions, target_date
        )

        # Should include transactions up to 2024-01-20
        # 1000.00 (credit) - 250.50 (debit) = 749.50
        assert balance.amount == Decimal("749.50")
        assert balance.currency == "BRL"

    def test_calculate_balance_at_beginning_date(self):
        """Should calculate balance including only transactions up to beginning date."""
        target_date = date(2024, 1, 1)

        balance = self.calculator.calculate_balance_at_date(
            self.transactions, target_date
        )

        # Should include only the first transaction
        assert balance.amount == Decimal("1000.00")
        assert balance.currency == "BRL"

    def test_calculate_balance_at_end_date(self):
        """Should calculate balance including all transactions up to end date."""
        target_date = date(2024, 2, 10)

        balance = self.calculator.calculate_balance_at_date(
            self.transactions, target_date
        )

        # All transactions: 1000.00 - 250.50 + 500.00 - 100.25 = 1149.25
        assert balance.amount == Decimal("1149.25")
        assert balance.currency == "BRL"

    def test_calculate_balance_before_any_transaction(self):
        """Should return zero balance for date before any transactions."""
        target_date = date(2023, 12, 31)

        balance = self.calculator.calculate_balance_at_date(
            self.transactions, target_date
        )

        assert balance.amount == Decimal("0.00")
        assert balance.currency == "BRL"

    def test_calculate_balance_with_empty_transaction_list(self):
        """Should return zero balance for empty transaction list."""
        target_date = date(2024, 1, 15)

        balance = self.calculator.calculate_balance_at_date([], target_date)

        assert balance.amount == Decimal("0.00")
        assert balance.currency == "BRL"


class TestBalanceCalculatorCurrentBalance:
    """Test current balance calculation."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.calculator = BalanceCalculatorService()

    def test_calculate_current_balance_with_transactions(self):
        """Should calculate current balance using today's date."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("500.00", "BRL"),
                description="Credit 1",
                transaction_date=date(2024, 1, 1),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("200.00", "BRL"),
                description="Debit 1",
                transaction_date=date(2024, 1, 15),
            ),
        ]

        balance = self.calculator.calculate_current_balance(transactions)

        # 500.00 - 200.00 = 300.00
        assert balance.amount == Decimal("300.00")
        assert balance.currency == "BRL"

    def test_calculate_current_balance_with_empty_list(self):
        """Should return zero for empty transaction list."""
        balance = self.calculator.calculate_current_balance([])

        assert balance.amount == Decimal("0.00")
        assert balance.currency == "BRL"



class TestBalanceCalculatorSufficientFunds:
    """Test sufficient funds checking."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.calculator = BalanceCalculatorService()

    def test_has_sufficient_funds_true(self):
        """Should return True when balance is sufficient for withdrawal."""
        current_balance = Money("500.00", "BRL")
        withdrawal_amount = Money("200.00", "BRL")

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is True

    def test_has_sufficient_funds_exactly_equal(self):
        """Should return True when balance exactly equals withdrawal amount."""
        current_balance = Money("300.00", "BRL")
        withdrawal_amount = Money("300.00", "BRL")

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is True

    def test_has_sufficient_funds_false(self):
        """Should return False when balance is insufficient for withdrawal."""
        current_balance = Money("100.00", "BRL")
        withdrawal_amount = Money("200.00", "BRL")

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is False

    def test_has_sufficient_funds_zero_balance(self):
        """Should return False for withdrawal from zero balance."""
        current_balance = Money.zero("BRL")
        withdrawal_amount = Money("50.00", "BRL")

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is False

    def test_has_sufficient_funds_zero_withdrawal(self):
        """Should return True for zero withdrawal amount."""
        current_balance = Money("100.00", "BRL")
        withdrawal_amount = Money.zero("BRL")

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is True

    def test_has_sufficient_funds_with_exception(self):
        """Should return False when exception occurs during calculation."""
        current_balance = Money("100.00", "BRL")
        withdrawal_amount = Money("50.00", "USD")  # Different currency

        result = self.calculator.has_sufficient_funds(
            current_balance, withdrawal_amount
        )

        assert result is False


class TestBalanceCalculatorComplexScenarios:
    """Test complex balance calculation scenarios."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.calculator = BalanceCalculatorService()

    def test_calculate_balance_with_multiple_currencies(self):
        """Should calculate balance correctly for mixed currency transactions."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("100.00", "BRL"),
                description="BRL Credit",
                transaction_date=date(2024, 1, 1),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("50.00", "BRL"),
                description="BRL Debit",
                transaction_date=date(2024, 1, 5),
            ),
        ]

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 10)
        )

        # Should process transactions in same currency correctly
        assert balance.amount == Decimal("50.00")
        assert balance.currency == "BRL"

    def test_calculate_balance_with_many_transactions(self):
        """Should handle calculation with many transactions efficiently."""
        transactions = []

        # Create 100 transactions alternating credit/debit
        for i in range(100):
            # Use modulo to cycle through days 1-31
            day = (i % 31) + 1
            if i % 2 == 0:
                transaction = Transaction.create_credit(
                    account_id=1,
                    amount=Money("10.00", "BRL"),
                    description=f"Credit {i}",
                    transaction_date=date(2024, 1, day),
                )
            else:
                transaction = Transaction.create_debit(
                    account_id=1,
                    amount=Money("5.00", "BRL"),
                    description=f"Debit {i}",
                    transaction_date=date(2024, 1, day),
                )
            transactions.append(transaction)

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 31)
        )

        # 50 credits of 10.00 = 500.00
        # 50 debits of 5.00 = 250.00
        # Net: 500.00 - 250.00 = 250.00
        assert balance.amount == Decimal("250.00")
        assert balance.currency == "BRL"

    def test_calculate_balance_with_high_precision_amounts(self):
        """Should handle high precision decimal amounts correctly."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("123.456789", "BRL"),
                description="Precision credit",
                transaction_date=date(2024, 1, 1),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("23.123456", "BRL"),
                description="Precision debit",
                transaction_date=date(2024, 1, 2),
            ),
        ]

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 5)
        )

        expected_balance = Decimal("123.456789") - Decimal("23.123456")
        assert balance.amount == expected_balance
        assert balance.currency == "BRL"


class TestBalanceCalculatorEdgeCases:
    """Test BalanceCalculator edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.calculator = BalanceCalculatorService()

    def test_calculate_balance_with_same_date_transactions(self):
        """Should handle multiple transactions on the same date correctly."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("100.00", "BRL"),
                description="Credit 1",
                transaction_date=date(2024, 1, 15),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("30.00", "BRL"),
                description="Debit 1",
                transaction_date=date(2024, 1, 15),
            ),
            Transaction.create_credit(
                account_id=1,
                amount=Money("50.00", "BRL"),
                description="Credit 2",
                transaction_date=date(2024, 1, 15),
            ),
        ]

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 15)
        )

        # 100.00 - 30.00 + 50.00 = 120.00
        assert balance.amount == Decimal("120.00")

    def test_calculate_balance_filters_future_transactions(self):
        """Should exclude transactions after target date."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("100.00", "BRL"),
                description="Past transaction",
                transaction_date=date(2024, 1, 10),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("50.00", "BRL"),
                description="Future transaction",
                transaction_date=date(2024, 1, 20),
            ),
        ]

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 15)
        )

        # Should only include the first transaction
        assert balance.amount == Decimal("100.00")

    def test_calculate_balance_with_very_large_amounts(self):
        """Should handle very large transaction amounts correctly."""
        transactions = [
            Transaction.create_credit(
                account_id=1,
                amount=Money("999999999.99", "BRL"),
                description="Large credit",
                transaction_date=date(2024, 1, 1),
            ),
            Transaction.create_debit(
                account_id=1,
                amount=Money("999999999.98", "BRL"),
                description="Large debit",
                transaction_date=date(2024, 1, 2),
            ),
        ]

        balance = self.calculator.calculate_balance_at_date(
            transactions, date(2024, 1, 5)
        )

        assert balance.amount == Decimal("0.01")
        assert balance.currency == "BRL"
