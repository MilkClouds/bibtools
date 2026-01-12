"""Rate limiter for API requests."""

import threading
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class RateLimiter:
    """Thread-safe rate limiter that ensures minimum interval between calls.

    Tracks the time of the last request and enforces a minimum delay before
    the next request. Thread-safe for concurrent usage.

    Example:
        limiter = RateLimiter(min_interval=1.0)

        # These calls will be spaced at least 1 second apart
        result1 = limiter.execute(lambda: api.get("/paper/1"))
        result2 = limiter.execute(lambda: api.get("/paper/2"))
    """

    def __init__(self, min_interval: float = 1.0):
        """Initialize rate limiter.

        Args:
            min_interval: Minimum seconds between requests.
        """
        self.min_interval = min_interval
        self._last_request_time: float = 0.0
        self._lock = threading.Lock()

    def execute(self, func: Callable[[], T]) -> T:
        """Execute function with rate limiting.

        Waits if needed, executes the function, then marks completion.
        The interval is measured from request completion to next request start.
        Uses lock to ensure proper serialization of rate-limited calls.

        Args:
            func: Function to execute.

        Returns:
            Result of the function.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            wait_time = max(0.0, self.min_interval - elapsed)

            if wait_time > 0:
                time.sleep(wait_time)

            try:
                return func()
            finally:
                self._last_request_time = time.monotonic()

    def reset(self) -> None:
        """Reset the rate limiter state."""
        with self._lock:
            self._last_request_time = 0.0


# Global rate limiters for Semantic Scholar API
# API key: 1 request/second
# No API key: 100 requests/5 minutes (~3 seconds between requests)
_rate_limiters: dict[str, RateLimiter] = {}
_global_lock = threading.Lock()


def get_rate_limiter(api_key: str | None = None) -> RateLimiter:
    """Get or create a rate limiter for the given API key.

    Rate limiters are shared per API key to ensure rate limits are
    respected across multiple client instances.

    Args:
        api_key: API key (or None for unauthenticated).

    Returns:
        Rate limiter instance.
    """
    key = api_key or "__no_key__"
    min_interval = 1.0 if api_key else 3.0

    with _global_lock:
        if key not in _rate_limiters:
            _rate_limiters[key] = RateLimiter(min_interval=min_interval)
        return _rate_limiters[key]


def reset_all_rate_limiters() -> None:
    """Reset all global rate limiters.

    Useful for testing to ensure test isolation. Each test can call this
    in setup to start with fresh rate limiter state.
    """
    with _global_lock:
        _rate_limiters.clear()
