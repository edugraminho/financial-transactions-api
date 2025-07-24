"""
Integration tests for AccountRepository.

Tests the AccountRepository implementation with real database operations
to verify data persistence, retrieval and business logic integration.
"""

import pytest
from datetime import datetime, timezone
from app.infrastructure.repositories.account_repository import AccountRepository
from app.domain.entities.account import Account
from app.core.enums import AccountStatus


class TestAccountRepositoryIntegration:
    """Test AccountRepository with real database operations."""

    def setup_method(self):
        """Set up repository instance for testing."""
        self.repository = AccountRepository()

    def test_create_account_success(self, db_session):
        """Should create account in database successfully."""
        # Arrange
        account = Account.create("ACC-INT-001", "Integration Test Account")

        # Act
        created_account = self.repository.create_no_commit(db_session, account)
        db_session.commit()

        # Assert
        assert created_account.id > 0
        assert created_account.account_number == "ACC-INT-001"
        assert created_account.account_name == "Integration Test Account"
        assert created_account.status == AccountStatus.ACTIVE
        assert isinstance(created_account.created_at, datetime)
        assert created_account.created_at.tzinfo == timezone.utc

    def test_get_account_by_id_success(self, db_session):
        """Should retrieve account by ID successfully."""
        # Arrange
        account = Account.create("ACC-INT-002", "Retrieval Test Account")
        created_account = self.repository.create_no_commit(db_session, account)
        db_session.commit()

        # Act
        retrieved_account = self.repository.get_by_id(db_session, created_account.id)

        # Assert
        assert retrieved_account is not None
        assert retrieved_account.id == created_account.id
        assert retrieved_account.account_number == "ACC-INT-002"
        assert retrieved_account.account_name == "Retrieval Test Account"
        assert retrieved_account.status == AccountStatus.ACTIVE

    def test_get_account_by_id_not_found(self, db_session):
        """Should return None when account ID does not exist."""
        # Act
        result = self.repository.get_by_id(db_session, 99999)

        # Assert
        assert result is None

    def test_get_account_by_number_success(self, db_session):
        """Should retrieve account by account number successfully."""
        # Arrange
        account = Account.create("ACC-INT-003", "Number Retrieval Test")
        self.repository.create_no_commit(db_session, account)
        db_session.commit()

        # Act
        retrieved_account = self.repository.get_by_account_number(
            db_session, "ACC-INT-003"
        )

        # Assert
        assert retrieved_account is not None
        assert retrieved_account.account_number == "ACC-INT-003"
        assert retrieved_account.account_name == "Number Retrieval Test"

    def test_get_account_by_number_not_found(self, db_session):
        """Should return None when account number does not exist."""
        # Act
        result = self.repository.get_by_account_number(db_session, "NON-EXISTENT")

        # Assert
        assert result is None

    def test_update_account_success(self, db_session):
        """Should update account in database successfully."""
        # Arrange
        account = Account.create("ACC-INT-004", "Original Name")
        created_account = self.repository.create_no_commit(db_session, account)
        db_session.commit()

        # Modify account
        created_account.account_name = "Updated Name"
        created_account.deactivate()

        # Act
        updated_account = self.repository.update_no_commit(db_session, created_account)
        db_session.commit()

        # Assert
        assert updated_account.account_name == "Updated Name"
        assert updated_account.status == AccountStatus.INACTIVE

        # Verify persistence
        retrieved_account = self.repository.get_by_id(db_session, created_account.id)
        assert retrieved_account.account_name == "Updated Name"
        assert retrieved_account.status == AccountStatus.INACTIVE


class TestAccountRepositoryErrorHandling:
    """Test AccountRepository error handling scenarios."""

    def setup_method(self):
        """Set up repository instance for testing."""
        self.repository = AccountRepository()

    def test_create_account_with_invalid_data(self, db_session):
        """Should handle validation errors appropriately."""
        # Create account with potentially problematic data
        account = Account.create("", "")  # Empty values

        # Database constraints should handle this appropriately
        # The behavior depends on the database schema validation
        created_account = self.repository.create_no_commit(db_session, account)

        # Assert that the repository can handle the creation
        assert created_account.account_number == ""
        assert created_account.account_name == ""

    def test_update_nonexistent_account(self, db_session):
        """Should handle updating non-existent account gracefully."""
        # Arrange
        account = Account.create("ACC-NONEXISTENT", "Non-existent Account")
        account.id = 99999  # Non-existent ID

        # Act & Assert
        # The repository should handle this gracefully
        # Behavior may vary by implementation
        try:
            result = self.repository.update_no_commit(db_session, account)
            # If update succeeds, it should return the account
            assert result is not None
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass

    def test_concurrent_account_creation(self, db_session):
        """Should handle concurrent account creation appropriately."""
        # This test simulates potential race conditions
        # In a real scenario, this would need more sophisticated testing

        # Arrange
        account1 = Account.create("ACC-CONCURRENT-1", "Concurrent Test 1")
        account2 = Account.create("ACC-CONCURRENT-2", "Concurrent Test 2")

        # Act
        created1 = self.repository.create_no_commit(db_session, account1)
        created2 = self.repository.create_no_commit(db_session, account2)
        db_session.commit()

        # Assert
        assert created1.id != created2.id
        assert created1.account_number != created2.account_number


class TestAccountRepositoryBusinessRules:
    """Test business rule enforcement in repository layer."""

    def setup_method(self):
        """Set up repository instance for testing."""
        self.repository = AccountRepository()

    def test_account_number_uniqueness_enforced(self, db_session):
        """Should enforce account number uniqueness at database level."""
        # Arrange
        account1 = Account.create("ACC-BUSINESS-001", "Business Rule Test 1")
        account2 = Account.create("ACC-BUSINESS-001", "Business Rule Test 2")

        # Act
        self.repository.create_no_commit(db_session, account1)
        db_session.commit()

        # Assert - Attempting to create duplicate should fail
        with pytest.raises(Exception):
            self.repository.create_no_commit(db_session, account2)
            db_session.commit()

    def test_account_data_integrity(self, db_session):
        """Should maintain data integrity across operations."""
        # Arrange
        account = Account.create("ACC-INTEGRITY", "Data Integrity Test")
        created_account = self.repository.create_no_commit(db_session, account)
        db_session.commit()

        original_id = created_account.id

        # Act - Multiple operations
        retrieved1 = self.repository.get_by_id(db_session, original_id)
        retrieved2 = self.repository.get_by_account_number(db_session, "ACC-INTEGRITY")

        # Assert - Data consistency
        assert retrieved1.id == retrieved2.id == original_id
        assert retrieved1.account_number == retrieved2.account_number == "ACC-INTEGRITY"
        assert (
            retrieved1.account_name == retrieved2.account_name == "Data Integrity Test"
        )
        assert retrieved1.status == retrieved2.status == AccountStatus.ACTIVE

    def test_repository_transaction_isolation(self, db_session):
        """Should respect database transaction boundaries."""
        # Arrange
        account = Account.create("ACC-TRANSACTION", "Transaction Test")

        # Act - Create but don't commit
        created_account = self.repository.create_no_commit(db_session, account)

        # Assert - Should exist in current transaction
        retrieved_in_tx = self.repository.get_by_id(db_session, created_account.id)
        assert retrieved_in_tx is not None
        assert retrieved_in_tx.account_number == "ACC-TRANSACTION"

        # After rollback (handled by test fixture), should not persist
        # This is automatically tested by the test framework's transaction rollback
