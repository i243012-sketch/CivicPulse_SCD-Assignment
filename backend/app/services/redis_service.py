"""Redis service for caching and rate limiting."""
import hashlib
import json
from typing import Any

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisService:
    """Service for Redis operations."""

    def __init__(self) -> None:
        """Initialize Redis connection."""
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get(self, key: str) -> str | None:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Value if exists, None otherwise
        """
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int) -> bool:
        """
        Set value in Redis with TTL.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.setex(key, ttl, value)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def increment(self, key: str, ttl: int | None = None) -> int | None:
        """
        Increment counter in Redis.
        
        Args:
            key: Counter key
            ttl: Optional TTL for the key (only set on first increment)
            
        Returns:
            New counter value, or None on error
        """
        try:
            value = self.client.incr(key)
            if ttl and value == 1:  # First increment, set TTL
                self.client.expire(key, ttl)
            return value
        except redis.RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    def check_rate_limit(self, client_ip: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Check if client has exceeded rate limit.
        
        Args:
            client_ip: Client IP address
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        key = f"rate_limit:{client_ip}"
        count = self.increment(key, ttl=window)

        if count is None:
            # Redis error - allow request but log warning
            logger.warning("Rate limit check failed, allowing request")
            return True, 0

        if count > limit:
            # Calculate retry after from TTL
            retry_after = self.client.ttl(key)
            return False, retry_after if retry_after > 0 else window

        return True, 0

    def is_healthy(self) -> bool:
        """
        Check if Redis is reachable.
        
        Returns:
            True if Redis responds to PING, False otherwise
        """
        try:
            return self.client.ping()
        except redis.RedisError:
            return False

    @staticmethod
    def compute_content_hash(text: str, location: str) -> str:
        """
        Compute deterministic hash of complaint content.
        
        Args:
            text: Complaint text
            location: Complaint location
            
        Returns:
            SHA256 hash as hex string
        """
        content = f"{text}|{location}"
        return hashlib.sha256(content.encode()).hexdigest()
