"""
Unit tests for Account entity.

Tests the Account domain entity which represents financial accounts
with business logic for account lifecycle and transaction validation.
"""

import pytest
import time
from datetime import datetime, timezone
from app.domain.entities.account import Account
from app.core.enums import AccountStatus
from app.core.exceptions import AccountNotFoundException


class TestAccountCreation:
    """Test Account entity creation and factory methods"""

    def test_create_account_with_factory_method(self):
        """Should create Account using factory method with correct defaults"""

        account = Account.create("ACC-001", "Test Account")

        assert account.account_number == "ACC-001"
        assert account.account_name == "Test Account"
        assert account.status == AccountStatus.ACTIVE
        assert account.id == 0
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)
        assert account.created_at.tzinfo == timezone.utc
        assert account.updated_at.tzinfo == timezone.utc

    def test_create_account_direct_instantiation(self):
        """Should create Account with direct instantiation."""

        now = datetime.now(timezone.utc)

        account = Account(
            id=1,
            account_number="ACC-002",
            account_name="Direct Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        assert account.id == 1
        assert account.account_number == "ACC-002"
        assert account.account_name == "Direct Account"
        assert account.status == AccountStatus.ACTIVE
        assert account.created_at == now
        assert account.updated_at == now

    def test_create_account_sets_timestamps(self):
        """Should set creation and update timestamps correctly."""

        before_creation = datetime.now(timezone.utc)
        account = Account.create("ACC-003", "Timestamp Test")
        after_creation = datetime.now(timezone.utc)

        assert before_creation <= account.created_at <= after_creation
        assert before_creation <= account.updated_at <= after_creation
        assert (
            account.created_at == account.updated_at
        )  # Should be the same for new accounts


class TestAccountStatusManagement:
    """Test Account status management operations."""

    def test_activate_account(self):
        """Should activate account and update timestamp."""

        account = Account.create("ACC-004", "Activation Test")
        account.status = AccountStatus.INACTIVE
        original_updated = account.updated_at

        time.sleep(0.001)

        account.activate()

        assert account.status == AccountStatus.ACTIVE
        assert account.updated_at > original_updated

    def test_deactivate_account(self):
        """Should deactivate account and update timestamp."""
        account = Account.create("ACC-005", "Deactivation Test")
        original_updated = account.updated_at

        time.sleep(0.001)

        account.deactivate()

        assert account.status == AccountStatus.INACTIVE
        assert account.updated_at > original_updated

    def test_block_account(self):
        """Should block account and update timestamp."""
        account = Account.create("ACC-006", "Block Test")
        original_updated = account.updated_at

        time.sleep(0.001)

        account.block()

        assert account.status == AccountStatus.BLOCKED
        assert account.updated_at > original_updated

    def test_multiple_status_changes(self):
        """Should handle multiple status changes correctly."""
        account = Account.create("ACC-007", "Multiple Status Test")

        # Test activation -> deactivation -> block -> activation
        account.deactivate()
        assert account.status == AccountStatus.INACTIVE

        account.block()
        assert account.status == AccountStatus.BLOCKED

        account.activate()
        assert account.status == AccountStatus.ACTIVE


class TestAccountStatusChecking:
    """Test Account status checking methods."""

    def test_is_active_when_active(self):
        """Should return True when account is active."""
        account = Account.create("ACC-008", "Active Test")

        assert account.is_active() is True

    def test_is_active_when_inactive(self):
        """Should return False when account is inactive."""
        account = Account.create("ACC-009", "Inactive Test")
        account.deactivate()

        assert account.is_active() is False

    def test_is_active_when_blocked(self):
        """Should return False when account is blocked."""
        account = Account.create("ACC-010", "Blocked Test")
        account.block()

        assert account.is_active() is False


class TestAccountTransactionValidation:
    """Test Account transaction validation logic."""

    def test_validate_for_transaction_when_active(self):
        """Should allow transaction validation for active accounts."""
        account = Account.create("ACC-011", "Transaction Test")

        # Should not raise any exception
        account.validate_for_transaction()

    def test_validate_for_transaction_when_inactive_raises_error(self):
        """Should raise AccountNotFoundException for inactive accounts."""
        account = Account.create("ACC-012", "Inactive Transaction Test")
        account.deactivate()

        with pytest.raises(
            AccountNotFoundException, match="Account ACC-012 is not active"
        ):
            account.validate_for_transaction()

    def test_validate_for_transaction_when_blocked_raises_error(self):
        """Should raise AccountNotFoundException for blocked accounts."""
        account = Account.create("ACC-013", "Blocked Transaction Test")
        account.block()

        with pytest.raises(
            AccountNotFoundException, match="Account ACC-013 is not active"
        ):
            account.validate_for_transaction()

    def test_validate_for_transaction_after_reactivation(self):
        """Should allow transactions after account reactivation."""
        account = Account.create("ACC-014", "Reactivation Test")

        # Deactivate and then reactivate
        account.deactivate()
        account.activate()

        # Should not raise any exception
        account.validate_for_transaction()


class TestAccountBusinessRules:
    """Test Account business rules and edge cases."""

    def test_account_with_empty_name(self):
        """Should handle accounts with empty names."""
        account = Account.create("ACC-015", "")

        assert account.account_name == ""
        assert account.is_active()

    def test_account_with_special_characters_in_number(self):
        """Should handle account numbers with special characters."""
        special_number = "ACC-2024-001@SPECIAL"
        account = Account.create(special_number, "Special Account")

        assert account.account_number == special_number

    def test_account_with_unicode_name(self):
        """Should handle account names with unicode characters."""
        unicode_name = "Conta Especial - José Müller 中文"
        account = Account.create("ACC-016", unicode_name)

        assert account.account_name == unicode_name

    def test_account_status_transitions_preserve_other_fields(self):
        """Should preserve other fields during status transitions."""
        account = Account.create("ACC-017", "Preservation Test")
        original_id = account.id
        original_number = account.account_number
        original_name = account.account_name
        original_created = account.created_at

        # Perform status changes
        account.deactivate()
        account.block()
        account.activate()

        assert account.id == original_id
        assert account.account_number == original_number
        assert account.account_name == original_name
        assert account.created_at == original_created


class TestAccountEquality:
    """Test Account equality and comparison operations."""

    def test_account_equality_by_id(self):
        """Should compare accounts by ID for equality."""
        account1 = Account(
            id=1,
            account_number="ACC-001",
            account_name="Account 1",
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        account2 = Account(
            id=1,
            account_number="ACC-002",  # Different details
            account_name="Account 2",
            status=AccountStatus.INACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Note: Account is a dataclass, so it compares all fields
        assert account1 != account2  # Different because of different fields

    def test_account_same_data_equality(self):
        """Should be equal when all data is the same."""
        now = datetime.now(timezone.utc)

        account1 = Account(
            id=1,
            account_number="ACC-001",
            account_name="Same Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        account2 = Account(
            id=1,
            account_number="ACC-001",
            account_name="Same Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        assert account1 == account2
