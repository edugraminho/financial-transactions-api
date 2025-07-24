"""
Integration tests for API endpoints.

Tests the complete API stack including routing, validation, business logic,
database operations and response formatting with real HTTP requests.
"""

import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from app.domain.entities.account import Account
from app.domain.entities.transaction import Transaction
from app.domain.value_objects.money import Money
from app.core.enums import TransactionType


class TestAccountEndpoints:
    """Test account-related API endpoints."""

    def test_create_account_success(self, client: TestClient):
        """Should create account via API successfully."""
        # Arrange
        account_data = {
            "account_number": "API-TEST-01",
            "account_name": "API Test Account",
        }

        # Act
        response = client.post("/api/v1/accounts", json=account_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["account_number"] == "API-TEST-01"
        assert data["account_name"] == "API Test Account"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_get_account_by_id_not_found(self, client: TestClient):
        """Should return 404 for non-existent account ID."""
        # Act
        response = client.get("/api/v1/accounts/99999")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestTransactionEndpoints:
    """Test transaction-related API endpoints."""

    def test_create_credit_transaction_success(
        self, client: TestClient, test_account: Account
    ):
        """Should create credit transaction via API successfully."""
        # Arrange
        transaction_data = {
            "account_id": test_account.id,
            "amount": "500.75",
            "transaction_type": "credit",
            "description": "API Test Credit Transaction",
            "reference_id": "API-CREDIT-001",
        }

        # Act
        response = client.post("/api/v1/transactions", json=transaction_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["account_id"] == test_account.id
        assert data["amount"]["amount"] == "500.75"
        assert data["amount"]["currency"] == "BRL"
        assert data["transaction_type"] == "credit"
        assert data["description"] == "API Test Credit Transaction"
        assert data["reference_id"] == "API-CREDIT-001"
        assert "id" in data
        assert "transaction_date" in data
        assert "created_at" in data

    def test_create_debit_transaction_success(
        self, client: TestClient, test_account: Account
    ):
        """Should create debit transaction via API successfully."""
        # Arrange
        transaction_data = {
            "account_id": test_account.id,
            "amount": "250.50",
            "transaction_type": "debit",
            "description": "API Test Debit Transaction",
        }

        # Act
        response = client.post("/api/v1/transactions", json=transaction_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "debit"
        assert data["amount"]["amount"] == "250.50"
        assert data["reference_id"] is None

    def test_create_transaction_invalid_account_fails(self, client: TestClient):
        """Should fail when creating transaction for non-existent account."""
        # Arrange
        transaction_data = {
            "account_id": 99999,
            "amount": "100.00",
            "transaction_type": "credit",
            "description": "Invalid Account Transaction",
        }

        # Act
        response = client.post("/api/v1/transactions", json=transaction_data)

        # Assert
        assert response.status_code == 404
        assert "account not found" in response.json()["detail"].lower()

    def test_list_transactions_success(self, client: TestClient, sample_transactions):
        """Should list transactions via API successfully."""
        # Act
        account_id = sample_transactions[0].account_id
        response = client.get(f"/api/v1/transactions?account_id={account_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "pagination" in data
        assert len(data["transactions"]) > 0

        # Verify transaction structure
        transaction = data["transactions"][0]
        assert "id" in transaction
        assert "account_id" in transaction
        assert "amount" in transaction
        assert "transaction_type" in transaction
        assert "description" in transaction

    def test_list_transactions_with_filters(
        self, client: TestClient, sample_transactions
    ):
        """Should filter transactions via API parameters."""
        # Act - Filter by account
        account_id = sample_transactions[0].account_id
        response = client.get(f"/api/v1/transactions?account_id={account_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        transactions = data["transactions"]

        # All returned transactions should belong to the specified account
        assert all(tx["account_id"] == account_id for tx in transactions)


class TestBalanceEndpoints:
    """Test balance-related API endpoints."""

    def test_get_balance_success(self, client: TestClient, sample_transactions):
        """Should get account balance via API successfully."""
        # Act
        account_id = sample_transactions[0].account_id
        response = client.get(f"/api/v1/accounts/{account_id}/balance")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "account_id" in data
        assert "account_number" in data
        assert "account_name" in data
        assert "date" in data
        assert "source" in data

        # Verify balance structure
        balance = data["balance"]
        assert "amount" in balance
        assert "currency" in balance

        # Verify account info
        assert data["account_id"] == account_id

    def test_get_balance_with_date(self, client: TestClient, sample_transactions):
        """Should get balance for specific date via API."""
        # Act
        account_id = sample_transactions[0].account_id
        target_date = "2024-01-20"
        response = client.get(
            f"/api/v1/accounts/{account_id}/balance?target_date={target_date}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == target_date

    def test_get_balance_invalid_account_fails(self, client: TestClient):
        """Should fail when getting balance for non-existent account."""
        # Act
        response = client.get("/api/v1/accounts/99999/balance")

        # Assert
        assert response.status_code == 404
        assert "account not found" in response.json()["detail"].lower()


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json_body_fails(self, client: TestClient):
        """Should handle invalid JSON gracefully."""
        # Act
        response = client.post(
            "/api/v1/accounts",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422

    def test_unsupported_http_method_fails(self, client: TestClient):
        """Should return 405 for unsupported HTTP methods."""
        # Act
        response = client.patch("/api/v1/accounts")

        # Assert
        assert response.status_code == 405

    def test_invalid_route_fails(self, client: TestClient):
        """Should return 404 for invalid routes."""
        # Act
        response = client.get("/api/v1/nonexistent")

        # Assert
        assert response.status_code == 404

    def test_large_amount_handling(self, client: TestClient, test_account: Account):
        """Should handle large monetary amounts correctly."""
        # Arrange
        large_amount_data = {
            "account_id": test_account.id,
            "amount": "999999999.99",
            "transaction_type": "credit",
            "description": "Large amount transaction",
        }

        # Act
        response = client.post("/api/v1/transactions", json=large_amount_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["amount"]["amount"] == "999999999.99"

    def test_precision_handling(self, client: TestClient, test_account: Account):
        """Should handle decimal precision correctly."""
        # Arrange
        precision_data = {
            "account_id": test_account.id,
            "amount": "123.456789",
            "transaction_type": "credit",
            "description": "High precision transaction",
        }

        # Act
        response = client.post("/api/v1/transactions", json=precision_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        # The system should preserve the precision as provided
        assert "123.456789" in data["amount"]["amount"]
