"""API-specific dependencies for FastAPI routes."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.db_connection import get_db_transaction, get_db

# Database dependencies
DatabaseDep = Annotated[Session, Depends(get_db_transaction)]
ReadOnlyDatabaseDep = Annotated[Session, Depends(get_db)]