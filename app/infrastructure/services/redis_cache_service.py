import json
import redis
from typing import Optional
from datetime import date
from decimal import Decimal
from app.application.services.cache_service import ICacheService
from app.domain.value_objects.money import Money
from app.core.config import settings


class RedisCacheService(ICacheService):
    """Redis cache service."""

    def __init__(self, redis_client: redis.Redis = None):
        """Initialize Redis cache service."""

        if redis_client is None:
            self.redis = redis.from_url(settings.redis_url)
        else:
            self.redis = redis_client

    def get_balance(self, account_id: int, target_date: date) -> Optional[Money]:
        """Get cached balance for account at specific date."""

        try:
            cache_key = self.get_cache_key(account_id, target_date)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                data = json.loads(cached_data.decode("utf-8"))
                amount = Decimal(data["amount"])
                currency = data.get("currency", "BRL")
                return Money(amount, currency)

            return None
        except Exception:
            return None

    def set_balance(
        self, account_id: int, target_date: date, balance: Money, ttl: int = 3600
    ) -> None:
        """Cache balance for account at specific date with TTL"""

        try:
            cache_key = self.get_cache_key(account_id, target_date)
            cache_data = {"amount": str(balance.amount), "currency": balance.currency}

            self.redis.setex(cache_key, ttl, json.dumps(cache_data))
        except Exception:
            pass

    def invalidate_account_cache(self, account_id: int) -> None:
        """Invalidate all cache entries for account"""
        try:
            # Use pattern matching to find all cache keys for this account
            pattern = f"balance:account:{account_id}:*"

            # Get all matching
            keys = self.redis.keys(pattern)

            # Delete all matching
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass

    def get_cache_key(self, account_id: int, target_date: date) -> str:
        """Generate cache key for balance"""

        date_str = target_date.isoformat()
        return f"balance:account:{account_id}:date:{date_str}"

    def ping(self) -> bool:
        """Check if Redis connection is healthy"""

        try:
            self.redis.ping()
            return True
        except Exception:
            return False

    def clear_all(self) -> None:
        """Clear all cache entries"""

        try:
            self.redis.flushdb()
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Get cache statistics."""

        try:
            info = self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except Exception:
            return {}
