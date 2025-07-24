from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from app.domain.value_objects.money import Money


class ICacheService(ABC):
    """Interface for cache operations."""

    @abstractmethod
    def get_balance(self, account_id: int, target_date: date) -> Optional[Money]:
        """Get cached balance for account at specific date."""
        pass

    @abstractmethod
    def set_balance(
        self, account_id: int, target_date: date, balance: Money, ttl: int = 3600
    ) -> None:
        """Cache balance for account at specific date with TTL."""
        pass

    @abstractmethod
    def invalidate_account_cache(self, account_id: int) -> None:
        """Invalidate all cache entries for account."""
        pass

    @abstractmethod
    def get_cache_key(self, account_id: int, target_date: date) -> str:
        """Generate cache key for balance."""
        pass


class CacheService:
    """Application service for cache operations coordination."""

    def __init__(self, cache_impl: ICacheService):
        self.cache = cache_impl

    def get_cached_balance(self, account_id: int, target_date: date) -> Optional[Money]:
        """Get balance from cache with error handling."""
        try:
            return self.cache.get_balance(account_id, target_date)
        except Exception:
            # errors not break the application
            return None

    def cache_balance(self, account_id: int, target_date: date, balance: Money) -> None:
        """Cache balance with appropriate TTL based on date."""
        try:
            # Historical dates get longer TTL (24 hours)
            # Current date gets shorter TTL (1 hour)
            ttl = 86400 if target_date < date.today() else 3600
            self.cache.set_balance(account_id, target_date, balance, ttl)
        except Exception:
            # errors not break the application
            pass

    def invalidate_account(self, account_id: int) -> None:
        """Invalidate account cache with error handling."""
        try:
            self.cache.invalidate_account_cache(account_id)
        except Exception:
            # errors not break the application
            pass
