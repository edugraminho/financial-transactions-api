"""
Pytest configuration and shared fixtures for testing.

This module provides comprehensive test fixtures for unit and integration testing,
including database setup, dependency injection, and test data factories.
"""

import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Generator, Iterator
from unittest.mock import Mock

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enums import TransactionType
from app.database.db_connection import get_db
from app.domain.entities.account import Account
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.infrastructure.repositories.account_repository import AccountRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository
from app.infrastructure.repositories.balance_snapshot_repository import (
    BalanceSnapshotRepository,
)
from app.infrastructure.services.redis_cache_service import RedisCacheService
from app.main import app
from app.models.models import Base


@pytest.fixture(scope="session")
def temp_db() -> Generator[str, None, None]:
    """Create temporary SQLite database for testing."""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    yield f"sqlite:///{temp_db_path}"

    # Cleanup
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def test_engine(temp_db: str):
    """Create test database engine with in-memory SQLite."""

    engine = create_engine(
        temp_db,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create fresh database session for each test with automatic rollback."""

    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to transaction
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def mock_redis() -> Mock:
    """Create mock Redis client for testing cache functionality."""

    mock_redis = Mock(spec=redis.Redis)
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False

    return mock_redis


@pytest.fixture
def mock_cache_service(mock_redis) -> Mock:
    """Create mock cache service for testing."""

    mock_service = Mock(spec=RedisCacheService)
    mock_service.get_cached_balance.return_value = None
    mock_service.cache_balance.return_value = None
    mock_service.invalidate_account.return_value = None

    return mock_service


@pytest.fixture
def account_repository(db_session: Session) -> AccountRepository:
    """Create account repository instance for testing."""
    return AccountRepository()


@pytest.fixture
def transaction_repository(db_session: Session) -> TransactionRepository:
    """Create transaction repository instance for testing."""
    return TransactionRepository()


@pytest.fixture
def balance_snapshot_repository(db_session: Session) -> BalanceSnapshotRepository:
    """Create balance snapshot repository instance for testing."""
    return BalanceSnapshotRepository()


@pytest.fixture
def test_account(account_repository: AccountRepository, db_session: Session) -> Account:
    """Create test account in database."""

    account = Account.create(account_number="TEST-001", account_name="Test Account")

    created_account = account_repository.create_no_commit(db_session, account)
    db_session.commit()

    return created_account


@pytest.fixture
def test_account_inactive(
    account_repository: AccountRepository, db_session: Session
) -> Account:
    """Create inactive test account in database."""

    account = Account.create(
        account_number="TEST-002", account_name="Inactive Test Account"
    )
    account.deactivate()

    created_account = account_repository.create_no_commit(db_session, account)
    db_session.commit()

    return created_account


@pytest.fixture
def sample_money() -> Money:
    """Create sample money object for testing."""
    return Money(Decimal("100.50"), "BRL")


@pytest.fixture
def sample_transaction_data() -> dict:
    """Create sample transaction data for testing."""
    return {
        "account_id": 1,
        "amount": Money(Decimal("250.75"), "BRL"),
        "transaction_type": TransactionType.CREDIT,
        "description": "Test transaction",
        "transaction_date": date.today(),
        "reference_id": "TEST-REF-001",
    }


@pytest.fixture
def sample_transactions(
    test_account: Account,
    transaction_repository: TransactionRepository,
    db_session: Session,
) -> list[Transaction]:
    """Create sample transactions for testing."""

    transactions_data = [
        {
            "account_id": test_account.id,
            "amount": Money(Decimal("1000.00"), "BRL"),
            "transaction_type": TransactionType.CREDIT,
            "description": "Initial deposit",
            "transaction_date": date(2024, 1, 1),
            "reference_id": "INIT-001",
        },
        {
            "account_id": test_account.id,
            "amount": Money(Decimal("250.50"), "BRL"),
            "transaction_type": TransactionType.DEBIT,
            "description": "Purchase",
            "transaction_date": date(2024, 1, 15),
            "reference_id": "PUR-001",
        },
        {
            "account_id": test_account.id,
            "amount": Money(Decimal("500.00"), "BRL"),
            "transaction_type": TransactionType.CREDIT,
            "description": "Salary",
            "transaction_date": date(2024, 1, 30),
            "reference_id": "SAL-001",
        },
    ]

    created_transactions = []
    for tx_data in transactions_data:
        transaction = Transaction(
            id=0,
            account_id=tx_data["account_id"],
            amount=tx_data["amount"],
            transaction_type=tx_data["transaction_type"],
            description=tx_data["description"],
            transaction_date=tx_data["transaction_date"],
            created_at=datetime.now(timezone.utc),
            reference_id=tx_data["reference_id"],
        )

        created_tx = transaction_repository.create_no_commit(db_session, transaction)
        created_transactions.append(created_tx)

    db_session.commit()
    return created_transactions


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Create FastAPI test client with dependency overrides."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()


# Utility fixtures for date/time testing
@pytest.fixture
def fixed_date():
    """Fixed date for consistent testing."""
    return date(2024, 1, 15)


@pytest.fixture
def fixed_datetime():
    """Fixed datetime for consistent testing."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


# Error testing fixtures
@pytest.fixture
def invalid_money_data():
    """Invalid money data for error testing."""
    return [
        {"amount": -100, "currency": "BRL"},
        {"amount": "invalid", "currency": "BRL"},
        {"amount": 100, "currency": ""},
    ]


@pytest.fixture
def invalid_transaction_data():
    """Invalid transaction data for error testing."""
    return [
        {"amount": Money(Decimal("0"), "BRL"), "description": "Zero amount"},
        {"amount": Money(Decimal("100"), "BRL"), "description": ""},
        {"amount": Money(Decimal("100"), "BRL"), "description": "x" * 501},
    ]
