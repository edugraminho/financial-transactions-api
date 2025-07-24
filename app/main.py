from fastapi import FastAPI
from app.database.db_connection import create_tables
from app.api.routes import transaction_routes, balance_routes, account_routes

app = FastAPI(
    title="Financial Transactions API",
    description="API for managing financial transactions in checking accounts",
    version="1.0.0",
)

# Include API routes
app.include_router(account_routes.router, prefix="/api/v1")
app.include_router(transaction_routes.router, prefix="/api/v1")
app.include_router(balance_routes.router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup."""
    create_tables()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "financial-transactions-api"}
