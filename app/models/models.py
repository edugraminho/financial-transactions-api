from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Enum as SQLEnum,
    Date,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.core.enums import TransactionType, AccountStatus

Base = declarative_base()


class AccountModel(Base):
    """SQLAlchemy model for financial accounts."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(50), nullable=False, unique=True)
    account_name = Column(String(255), nullable=False)
    status = Column(
        SQLEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE
    )
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_account_number", "account_number"),
        Index("idx_status", "status"),
    )


class TransactionModel(Base):
    """SQLAlchemy model for financial transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    description = Column(Text, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    reference_id = Column(String(255), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_account_date", "account_id", "transaction_date"),
        Index("idx_date", "transaction_date"),
        Index("idx_reference", "reference_id"),
    )


class BalanceSnapshotModel(Base):
    """SQLAlchemy model for balance snapshots."""

    __tablename__ = "balance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False)
    balance_amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    transaction_count = Column(Integer, default=0)
    snapshot_type = Column(String(20), default="daily")

    # Indexes for performance
    __table_args__ = (
        Index("idx_snapshot_account_date", "account_id", "snapshot_date"),
        Index("idx_snapshot_date_type", "snapshot_date", "snapshot_type"),
        Index(
            "idx_snapshot_account_date_desc",
            "account_id",
            "snapshot_date",
            postgresql_using="btree",
        ),
    )
