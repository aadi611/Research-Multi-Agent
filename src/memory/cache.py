"""Redis cache with in-memory fallback."""
import json
import hashlib
import time
import os
from typing import Any


class ResearchCache:
    def __init__(self, redis_url: str = None, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._memory: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._redis = None

        url = redis_url or os.getenv("REDIS_URL")
        if url:
            try:
                import redis
                self._redis = redis.from_url(url, decode_responses=True)
                self._redis.ping()
                print("✅ Redis connected")
            except Exception as e:
                print(f"⚠️  Redis unavailable ({e}), using in-memory cache")
                self._redis = None

    def _make_key(self, query: str) -> str:
        return "research:" + hashlib.md5(query.lower().strip().encode()).hexdigest()

    def get(self, query: str) -> Any | None:
        key = self._make_key(query)

        if self._redis:
            try:
                data = self._redis.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass

        # In-memory fallback
        entry = self._memory.get(key)
        if entry:
            value, expires_at = entry
            if time.time() < expires_at:
                return value
            del self._memory[key]
        return None

    def set(self, query: str, value: Any) -> None:
        key = self._make_key(query)
        serialized = json.dumps(value, default=str)

        if self._redis:
            try:
                self._redis.setex(key, self.ttl, serialized)
                return
            except Exception:
                pass

        self._memory[key] = (value, time.time() + self.ttl)

    def clear(self) -> None:
        if self._redis:
            try:
                for key in self._redis.scan_iter("research:*"):
                    self._redis.delete(key)
            except Exception:
                pass
        self._memory.clear()
