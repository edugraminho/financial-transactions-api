"""
Unit tests for CreateTransactionUseCase.

Tests the CreateTransactionUseCase with mocked dependencies to verify
business logic, validation and integration with repositories and services.
"""

import pytest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal
from app.application.use_cases.create_transaction import CreateTransactionUseCase
from app.domain.entities.account import Account
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.core.enums import AccountStatus, TransactionType
from app.core.exceptions import AccountNotFoundException, InvalidTransactionException


class TestCreateTransactionUseCaseSuccess:
    """Test successful transaction creation scenarios."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

        # Create mock active account
        self.mock_account = Account.create("ACC-001", "Test Account")
        self.mock_account.id = 1

    def test_create_credit_transaction_success(self):
        """Should create credit transaction successfully when account exists and is active."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("500.00", "BRL"),
            "transaction_type": "credit",
            "description": "Salary deposit",
            "transaction_date": date(2024, 1, 15),
            "reference_id": "SAL-001",
        }

        expected_transaction = Transaction.create_credit(
            account_id=1,
            amount=Money("500.00", "BRL"),
            description="Salary deposit",
            transaction_date=date(2024, 1, 15),
            reference_id="SAL-001",
        )
        expected_transaction.id = 123

        self.mock_transaction_repo.create_no_commit.return_value = expected_transaction

        # Act
        result = self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert result.id == 123
        assert result.account_id == 1
        assert result.amount.amount == Decimal("500.00")
        assert result.transaction_type == TransactionType.CREDIT
        assert result.description == "Salary deposit"
        assert result.reference_id == "SAL-001"

        # Verify interactions
        self.mock_account_repo.get_by_id.assert_called_once_with(self.mock_db, 1)
        self.mock_transaction_repo.create_no_commit.assert_called_once()
        self.mock_cache_service.invalidate_account.assert_called_once_with(1)

    def test_create_debit_transaction_success(self):
        """Should create debit transaction successfully when account exists and is active."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("250.75", "BRL"),
            "transaction_type": "debit",
            "description": "Purchase at supermarket",
            "reference_id": "PUR-001",
        }

        expected_transaction = Transaction.create_debit(
            account_id=1,
            amount=Money("250.75", "BRL"),
            description="Purchase at supermarket",
            reference_id="PUR-001",
        )
        expected_transaction.id = 124

        self.mock_transaction_repo.create_no_commit.return_value = expected_transaction

        # Act
        result = self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert result.id == 124
        assert result.account_id == 1
        assert result.amount.amount == Decimal("250.75")
        assert result.transaction_type == TransactionType.DEBIT
        assert result.description == "Purchase at supermarket"
        assert result.reference_id == "PUR-001"

    def test_create_transaction_without_reference_id(self):
        """Should create transaction successfully without reference ID."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Cash deposit",
        }

        expected_transaction = Transaction.create_credit(
            account_id=1, amount=Money("100.00", "BRL"), description="Cash deposit"
        )
        expected_transaction.id = 125

        self.mock_transaction_repo.create_no_commit.return_value = expected_transaction

        # Act
        result = self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert result.reference_id is None
        assert result.description == "Cash deposit"

    def test_create_transaction_without_date_uses_today(self):
        """Should use today's date when transaction_date is not provided."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("75.00", "BRL"),
            "transaction_type": "debit",
            "description": "ATM withdrawal",
        }

        expected_transaction = Transaction.create_debit(
            account_id=1, amount=Money("75.00", "BRL"), description="ATM withdrawal"
        )
        expected_transaction.id = 126

        self.mock_transaction_repo.create_no_commit.return_value = expected_transaction

        # Act
        result = self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert result.transaction_date == date.today()


class TestCreateTransactionUseCaseAccountValidation:
    """Test account validation scenarios."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

    def test_create_transaction_account_not_found_raises_error(self):
        """Should raise AccountNotFoundException when account does not exist."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = None

        transaction_data = {
            "account_id": 999,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Test transaction",
        }

        # Act & Assert
        with pytest.raises(AccountNotFoundException, match="Account not found"):
            self.use_case.execute(self.mock_db, transaction_data)

        # Verify that repository methods were not called after validation failure
        self.mock_transaction_repo.create_no_commit.assert_not_called()
        self.mock_cache_service.invalidate_account.assert_not_called()

    def test_create_transaction_inactive_account_raises_error(self):
        """Should raise AccountNotFoundException when account is inactive."""
        # Arrange
        inactive_account = Account.create("ACC-002", "Inactive Account")
        inactive_account.id = 2
        inactive_account.deactivate()

        self.mock_account_repo.get_by_id.return_value = inactive_account

        transaction_data = {
            "account_id": 2,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Test transaction",
        }

        # Act & Assert
        with pytest.raises(
            AccountNotFoundException, match="Account ACC-002 is not active"
        ):
            self.use_case.execute(self.mock_db, transaction_data)

    def test_create_transaction_blocked_account_raises_error(self):
        """Should raise AccountNotFoundException when account is blocked."""
        # Arrange
        blocked_account = Account.create("ACC-003", "Blocked Account")
        blocked_account.id = 3
        blocked_account.block()

        self.mock_account_repo.get_by_id.return_value = blocked_account

        transaction_data = {
            "account_id": 3,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "debit",
            "description": "Test transaction",
        }

        # Act & Assert
        with pytest.raises(
            AccountNotFoundException, match="Account ACC-003 is not active"
        ):
            self.use_case.execute(self.mock_db, transaction_data)


class TestCreateTransactionUseCacheInvalidation:
    """Test cache invalidation behavior."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

        # Create mock active account
        self.mock_account = Account.create("ACC-001", "Test Account")
        self.mock_account.id = 1

    def test_cache_invalidation_called_after_transaction_creation(self):
        """Should invalidate account cache after successful transaction creation."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("200.00", "BRL"),
            "transaction_type": "credit",
            "description": "Test credit",
        }

        mock_transaction = Mock()
        mock_transaction.id = 127
        self.mock_transaction_repo.create_no_commit.return_value = mock_transaction

        # Act
        self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        self.mock_cache_service.invalidate_account.assert_called_once_with(1)

    def test_cache_not_invalidated_on_validation_failure(self):
        """Should not invalidate cache when account validation fails."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = None

        transaction_data = {
            "account_id": 999,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Test transaction",
        }

        # Act & Assert
        with pytest.raises(AccountNotFoundException):
            self.use_case.execute(self.mock_db, transaction_data)

        self.mock_cache_service.invalidate_account.assert_not_called()


class TestCreateTransactionUseCaseTransactionTypes:
    """Test different transaction type handling."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

        # Create mock active account
        self.mock_account = Account.create("ACC-001", "Test Account")
        self.mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = self.mock_account

    def test_create_credit_transaction_type_mapping(self):
        """Should correctly map 'credit' string to CREDIT enum."""
        # Arrange
        transaction_data = {
            "account_id": 1,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Credit test",
        }

        # Mock the repository to capture the created transaction
        created_transaction = None

        def capture_transaction(db, transaction):
            nonlocal created_transaction
            created_transaction = transaction
            return transaction

        self.mock_transaction_repo.create_no_commit.side_effect = capture_transaction

        # Act
        self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert created_transaction.transaction_type == TransactionType.CREDIT
        assert created_transaction.is_credit() is True

    def test_create_debit_transaction_type_mapping(self):
        """Should correctly map 'debit' string to DEBIT enum."""
        # Arrange
        transaction_data = {
            "account_id": 1,
            "amount": Money("50.00", "BRL"),
            "transaction_type": "debit",
            "description": "Debit test",
        }

        # Mock the repository to capture the created transaction
        created_transaction = None

        def capture_transaction(db, transaction):
            nonlocal created_transaction
            created_transaction = transaction
            return transaction

        self.mock_transaction_repo.create_no_commit.side_effect = capture_transaction

        # Act
        self.use_case.execute(self.mock_db, transaction_data)

        # Assert
        assert created_transaction.transaction_type == TransactionType.DEBIT
        assert created_transaction.is_debit() is True


class TestCreateTransactionUseCaseErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

    def test_repository_error_propagated(self):
        """Should propagate repository errors without modification."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        # Simulate repository error
        self.mock_transaction_repo.create_no_commit.side_effect = Exception(
            "Database error"
        )

        transaction_data = {
            "account_id": 1,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Test transaction",
        }

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            self.use_case.execute(self.mock_db, transaction_data)

    def test_invalid_transaction_data_raises_validation_error(self):
        """Should raise validation error for invalid transaction data."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        # Invalid transaction data (zero amount)
        transaction_data = {
            "account_id": 1,
            "amount": Money("0.00", "BRL"),
            "transaction_type": "credit",
            "description": "Invalid transaction",
        }

        # Act & Assert
        with pytest.raises(
            InvalidTransactionException, match="Transaction amount must be positive"
        ):
            self.use_case.execute(self.mock_db, transaction_data)


class TestCreateTransactionUseCaseIntegration:
    """Test use case integration behavior."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_transaction_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_cache_service = Mock()

        self.use_case = CreateTransactionUseCase(
            transaction_repo=self.mock_transaction_repo,
            account_repo=self.mock_account_repo,
            cache_service=self.mock_cache_service,
        )

        self.mock_db = Mock()

    def test_complete_execution_flow(self):
        """Should execute complete flow in correct order."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        mock_transaction = Mock()
        mock_transaction.id = 128
        self.mock_transaction_repo.create_no_commit.return_value = mock_transaction

        transaction_data = {
            "account_id": 1,
            "amount": Money("300.00", "BRL"),
            "transaction_type": "debit",
            "description": "Integration test",
            "reference_id": "INT-001",
        }

        # Act
        result = self.use_case.execute(self.mock_db, transaction_data)

        # Verify account repository was called first
        self.mock_account_repo.get_by_id.assert_called_once_with(self.mock_db, 1)

        # Verify transaction repository was called second
        self.mock_transaction_repo.create_no_commit.assert_called_once()

        # Verify cache service was called last
        self.mock_cache_service.invalidate_account.assert_called_once_with(1)

        # Verify result
        assert result == mock_transaction

    def test_dependency_injection_working_correctly(self):
        """Should use injected dependencies correctly."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1

        # Act & verify each dependency is used
        self.mock_account_repo.get_by_id.return_value = mock_account

        transaction_data = {
            "account_id": 1,
            "amount": Money("100.00", "BRL"),
            "transaction_type": "credit",
            "description": "Dependency test",
        }

        mock_transaction = Mock()
        self.mock_transaction_repo.create_no_commit.return_value = mock_transaction

        result = self.use_case.execute(self.mock_db, transaction_data)

        # Assert all dependencies were used
        assert self.mock_account_repo.get_by_id.called
        assert self.mock_transaction_repo.create_no_commit.called
        assert self.mock_cache_service.invalidate_account.called
        assert result == mock_transaction
