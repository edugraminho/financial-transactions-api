from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings configuration."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/financial_db"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
