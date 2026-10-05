import threading
import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: str
    expires_at: float


class ResponseCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> str | None:
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            if entry.expires_at < now:
                self._store.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return entry.value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl_seconds)

    def flush(self) -> int:
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def size(self) -> int:
        with self._lock:
            return len(self._store)


response_cache = ResponseCache()
