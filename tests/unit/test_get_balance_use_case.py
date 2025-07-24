"""
Unit tests for GetBalanceUseCase.

Tests the GetBalanceUseCase with mocked dependencies to verify
cache strategies, balance calculation logic and performance optimizations.
"""

import pytest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.domain.entities.account import Account
from app.domain.entities.balance_snapshot import BalanceSnapshot
from app.domain.value_objects.money import Money
from app.core.exceptions import AccountNotFoundException


class TestGetBalanceUseCaseSuccess:
    """Test successful balance retrieval scenarios."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

        self.mock_db = Mock()

        # Create mock account
        self.mock_account = Account.create("ACC-001", "Test Account")
        self.mock_account.id = 1

    def test_get_balance_from_cache_hit(self):
        """Should return balance from cache when cache hit occurs."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account
        cached_balance = Money("1500.75", "BRL")
        self.mock_cache_service.get_cached_balance.return_value = cached_balance

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert
        assert result["balance"]["amount"] == "1500.75"
        assert result["balance"]["currency"] == "BRL"
        assert result["source"] == "cache"
        assert result["account"]["id"] == 1
        assert result["account"]["account_number"] == "ACC-001"
        assert result["target_date"] == target_date.isoformat()

        # Verify cache was checked
        self.mock_cache_service.get_cached_balance.assert_called_once_with(
            1, target_date
        )

        # Verify other methods were not called due to cache hit
        self.mock_snapshot_repo.get_latest_before_date.assert_not_called()
        self.mock_transaction_repo.get_balance_by_date.assert_not_called()

    def test_get_balance_from_snapshot(self):
        """Should calculate balance from snapshot when available."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account
        self.mock_cache_service.get_cached_balance.return_value = None  # Cache miss

        # Mock snapshot
        snapshot = BalanceSnapshot.create(
            account_id=1,
            snapshot_date=date(2024, 1, 10),
            balance_amount=Decimal("1000.00"),
        )
        self.mock_snapshot_repo.get_latest_before_date.return_value = snapshot

        # Mock balance calculation from snapshot
        calculated_balance = Money("1250.50", "BRL")
        self.use_case._calculate_from_snapshot = Mock(return_value=calculated_balance)

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert
        assert result["balance"]["amount"] == "1250.50"
        assert result["source"] == "snapshot"

        # Verify snapshot was used
        self.mock_snapshot_repo.get_latest_before_date.assert_called_once_with(
            self.mock_db, 1, target_date
        )
        self.use_case._calculate_from_snapshot.assert_called_once_with(
            self.mock_db, snapshot, 1, target_date
        )

        # Verify result was cached
        self.mock_cache_service.cache_balance.assert_called_once_with(
            1, target_date, calculated_balance
        )

    def test_get_balance_full_calculation(self):
        """Should perform full calculation when no cache or snapshot available."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account
        self.mock_cache_service.get_cached_balance.return_value = None  # Cache miss
        self.mock_snapshot_repo.get_latest_before_date.return_value = (
            None  # No snapshot
        )

        # Mock full calculation
        balance_amount = Decimal("850.25")
        self.mock_transaction_repo.get_balance_by_date.return_value = balance_amount

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert
        assert result["balance"]["amount"] == "850.25"
        assert result["source"] in ["calculated", "calculated+snapshot_created"]

        # Verify full calculation was performed
        self.mock_transaction_repo.get_balance_by_date.assert_called_once_with(
            self.mock_db, 1, target_date
        )

        # Verify result was cached
        calculated_balance = Money(balance_amount)
        self.mock_cache_service.cache_balance.assert_called_once_with(
            1, target_date, calculated_balance
        )

    def test_get_balance_with_snapshot_creation(self):
        """Should create snapshot when conditions are met and return calculated+snapshot_created source."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account
        self.mock_cache_service.get_cached_balance.return_value = None
        self.mock_snapshot_repo.get_latest_before_date.return_value = None

        balance_amount = Decimal("2000.00")
        self.mock_transaction_repo.get_balance_by_date.return_value = balance_amount

        # Mock snapshot service
        self.mock_snapshot_service.should_create_snapshot.return_value = True

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert
        assert result["source"] == "calculated+snapshot_created"
        assert result["balance"]["amount"] == "2000.00"

        # Verify snapshot creation was attempted
        self.mock_snapshot_service.should_create_snapshot.assert_called_once_with(
            self.mock_db, 1, target_date
        )
        self.mock_snapshot_service.create_daily_snapshot.assert_called_once_with(
            self.mock_db, 1, target_date
        )

    def test_get_balance_default_to_today(self):
        """Should use today's date when target_date is None."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = self.mock_account
        cached_balance = Money("500.00", "BRL")
        self.mock_cache_service.get_cached_balance.return_value = cached_balance

        # Act
        result = self.use_case.execute(self.mock_db, account_id=1, target_date=None)

        # Assert
        expected_date = date.today()
        assert result["target_date"] == expected_date.isoformat()

        # Verify today's date was used in cache lookup
        self.mock_cache_service.get_cached_balance.assert_called_once_with(
            1, expected_date
        )


class TestGetBalanceUseCaseAccountValidation:
    """Test account validation scenarios."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

        self.mock_db = Mock()

    def test_get_balance_account_not_found_raises_error(self):
        """Should raise AccountNotFoundException when account does not exist."""
        # Arrange
        self.mock_account_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(AccountNotFoundException, match="Account not found"):
            self.use_case.execute(
                self.mock_db, account_id=999, target_date=date(2024, 1, 15)
            )

        # Verify that no other services were called
        self.mock_cache_service.get_cached_balance.assert_not_called()
        self.mock_snapshot_repo.get_latest_before_date.assert_not_called()


class TestGetBalanceUseCaseCalculateFromSnapshot:
    """Test balance calculation from snapshot scenarios."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

        self.mock_db = Mock()

    def test_calculate_from_snapshot_same_date(self):
        """Should return snapshot balance when target date equals snapshot date."""
        # Arrange
        snapshot = BalanceSnapshot.create(
            account_id=1,
            snapshot_date=date(2024, 1, 15),
            balance_amount=Decimal("1000.00"),
        )
        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case._calculate_from_snapshot(
            self.mock_db, snapshot, 1, target_date
        )

        # Assert
        assert result.amount == Decimal("1000.00")
        assert result.currency == "BRL"

        # Verify no additional calculations were needed
        self.mock_transaction_repo.get_transactions_after_date.assert_not_called()

    def test_calculate_from_snapshot_with_delta(self):
        """Should calculate balance with delta when target date is after snapshot date."""
        # Arrange
        snapshot = BalanceSnapshot.create(
            account_id=1,
            snapshot_date=date(2024, 1, 10),
            balance_amount=Decimal("1000.00"),
        )
        target_date = date(2024, 1, 15)

        # Mock transactions after snapshot - create a credit transaction for +200.00
        from unittest.mock import Mock
        mock_transaction = Mock()
        mock_transaction.is_credit.return_value = True
        mock_transaction.amount = Money("200.00", "BRL")
        
        mock_transactions = [mock_transaction]
        self.mock_transaction_repo.list_by_account.return_value = mock_transactions

        # Act
        result = self.use_case._calculate_from_snapshot(
            self.mock_db, snapshot, 1, target_date
        )

        # Assert
        expected_balance = Money("1000.00", "BRL").add(Money("200.00", "BRL"))
        assert result.amount == expected_balance.amount

        # Verify transactions were retrieved
        self.mock_transaction_repo.list_by_account.assert_called_once()


class TestGetBalanceUseCaseErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

        self.mock_db = Mock()

    def test_snapshot_creation_failure_does_not_affect_result(self):
        """Should continue normally when snapshot creation fails."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        self.mock_cache_service.get_cached_balance.return_value = None
        self.mock_snapshot_repo.get_latest_before_date.return_value = None

        balance_amount = Decimal("750.00")
        self.mock_transaction_repo.get_balance_by_date.return_value = balance_amount

        # Mock snapshot service to fail
        self.mock_snapshot_service.should_create_snapshot.return_value = True
        self.mock_snapshot_service.create_daily_snapshot.side_effect = Exception(
            "Snapshot creation failed"
        )

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert - should still return calculated balance
        assert result["balance"]["amount"] == "750.00"
        assert result["source"] in ["calculated", "calculated+snapshot_created"]


class TestGetBalanceUseCaseBuildResponse:
    """Test response building functionality."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

    def test_build_response_structure(self):
        """Should build response with correct structure."""
        # Arrange
        account = Account.create("ACC-001", "Test Account")
        account.id = 1
        balance = Money("1234.56", "USD")
        target_date = date(2024, 1, 15)
        source = "test_source"

        # Act
        result = self.use_case._build_response(account, balance, target_date, source)

        # Assert
        assert result["account"]["id"] == 1
        assert result["account"]["account_number"] == "ACC-001"
        assert result["account"]["account_name"] == "Test Account"
        assert result["balance"]["amount"] == "1234.56"
        assert result["balance"]["currency"] == "USD"
        assert result["target_date"] == "2024-01-15"
        assert result["source"] == "test_source"

    def test_build_response_with_different_currencies(self):
        """Should handle different currencies correctly in response."""
        # Arrange
        account = Account.create("ACC-002", "Euro Account")
        account.id = 2
        balance = Money("999.99", "EUR")
        target_date = date(2024, 2, 29)
        source = "cache"

        # Act
        result = self.use_case._build_response(account, balance, target_date, source)

        # Assert
        assert result["balance"]["currency"] == "EUR"
        assert result["target_date"] == "2024-02-29"


class TestGetBalanceUseCaseIntegration:
    """Test use case integration behavior."""

    def setup_method(self):
        """Set up test dependencies and mocks."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.mock_snapshot_repo = Mock()
        self.mock_balance_calculator = Mock()
        self.mock_cache_service = Mock()
        self.mock_snapshot_service = Mock()

        self.use_case = GetBalanceUseCase(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_transaction_repo,
            snapshot_repo=self.mock_snapshot_repo,
            balance_calculator=self.mock_balance_calculator,
            cache_service=self.mock_cache_service,
            snapshot_service=self.mock_snapshot_service,
        )

        self.mock_db = Mock()

    def test_cache_aside_pattern_implementation(self):
        """Should implement cache-aside pattern correctly."""
        # Arrange
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        # Cache miss, then calculation, then cache set
        self.mock_cache_service.get_cached_balance.return_value = None
        self.mock_snapshot_repo.get_latest_before_date.return_value = None

        balance_amount = Decimal("1000.00")
        self.mock_transaction_repo.get_balance_by_date.return_value = balance_amount

        target_date = date(2024, 1, 15)

        # Act
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )

        # Assert cache-aside pattern
        # 1. Cache read attempt
        self.mock_cache_service.get_cached_balance.assert_called_once_with(
            1, target_date
        )

        # 2. Cache miss leads to calculation
        self.mock_transaction_repo.get_balance_by_date.assert_called_once()

        # 3. Result is cached
        calculated_balance = Money(balance_amount)
        self.mock_cache_service.cache_balance.assert_called_once_with(
            1, target_date, calculated_balance
        )

    def test_performance_optimization_layers(self):
        """Should demonstrate the three-layer performance optimization."""
        mock_account = Account.create("ACC-001", "Test Account")
        mock_account.id = 1
        self.mock_account_repo.get_by_id.return_value = mock_account

        target_date = date(2024, 1, 15)

        # Test Layer 1: Cache
        self.mock_cache_service.get_cached_balance.return_value = Money("100.00", "BRL")
        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )
        assert result["source"] == "cache"

        # Test Layer 2: Snapshot (cache miss)
        self.mock_cache_service.get_cached_balance.return_value = None
        snapshot = BalanceSnapshot.create(1, target_date, Decimal("200.00"))
        self.mock_snapshot_repo.get_latest_before_date.return_value = snapshot

        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )
        assert result["source"] == "snapshot"

        # Test Layer 3: Full calculation (cache miss + no snapshot)
        self.mock_snapshot_repo.get_latest_before_date.return_value = None
        self.mock_transaction_repo.get_balance_by_date.return_value = Decimal("300.00")

        result = self.use_case.execute(
            self.mock_db, account_id=1, target_date=target_date
        )
        assert result["source"] in ["calculated", "calculated+snapshot_created"]
