from typing import List
from datetime import date
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money


class BalanceCalculatorService:
    """Domain service for balance calculations with pure business logic"""

    def calculate_balance_at_date(
        self, transactions: List[Transaction], target_date: date
    ) -> Money:
        """Calculate account balance at specific date from transaction list"""

        balance = Money.zero()

        filtered_transactions = [
            t for t in transactions if t.transaction_date <= target_date
        ]

        for transaction in filtered_transactions:
            if transaction.is_credit():
                balance = balance.add(transaction.amount)
            else:
                balance = balance.subtract(transaction.amount)

        return balance

    def calculate_current_balance(self, transactions: List[Transaction]) -> Money:
        """Calculate current balance from all transactions"""
        return self.calculate_balance_at_date(transactions, date.today())

    def has_sufficient_funds(
        self, current_balance: Money, withdrawal_amount: Money
    ) -> bool:
        """Check if account has sufficient funds for withdrawal."""

        try:
            result_balance = current_balance.subtract(withdrawal_amount)
            return result_balance.amount >= 0
        except Exception:
            return False

    def calculate_daily_balances(
        self, transactions: List[Transaction], start_date: date, end_date: date
    ) -> dict:
        """Calculate daily balances for date range."""

        daily_balances = {}
        current_date = start_date

        while current_date <= end_date:
            balance = self.calculate_balance_at_date(transactions, current_date)
            daily_balances[current_date.isoformat()] = balance
            current_date = date.fromordinal(current_date.toordinal() + 1)

        return daily_balances

    def get_transaction_summary(self, transactions: List[Transaction]) -> dict:
        """Get summary statistics for transactions"""

        total_credits = Money.zero()
        total_debits = Money.zero()

        for transaction in transactions:
            if transaction.is_credit():
                total_credits = total_credits.add(transaction.amount)
            else:
                total_debits = total_debits.add(transaction.amount)

        return {
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_balance": total_credits.subtract(total_debits),
            "transaction_count": len(transactions),
        }
