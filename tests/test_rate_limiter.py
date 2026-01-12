"""Tests for rate_limiter module."""

import threading
import time


from bibtools.rate_limiter import RateLimiter, get_rate_limiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_first_call_no_wait(self):
        """First call should not wait."""
        limiter = RateLimiter(min_interval=1.0)
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # Should be nearly instant

    def test_second_call_waits_after_mark(self):
        """Second call should wait for min_interval after mark_request_done."""
        limiter = RateLimiter(min_interval=0.2)
        limiter.wait()
        limiter.mark_request_done()  # Simulate request completion
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.15  # Should wait ~0.2s (with some tolerance)
        assert elapsed < 0.4

    def test_no_wait_after_interval(self):
        """Should not wait if enough time has passed."""
        limiter = RateLimiter(min_interval=0.1)
        limiter.wait()
        limiter.mark_request_done()
        time.sleep(0.15)  # Wait longer than interval
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05  # Should be nearly instant

    def test_execute_returns_result(self):
        """Execute should return function result."""
        limiter = RateLimiter(min_interval=0.0)
        result = limiter.execute(lambda: 42)
        assert result == 42

    def test_execute_with_rate_limiting(self):
        """Execute should apply rate limiting."""
        limiter = RateLimiter(min_interval=0.2)
        limiter.execute(lambda: None)
        start = time.monotonic()
        limiter.execute(lambda: None)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.15

    def test_reset(self):
        """Reset should clear the last request time."""
        limiter = RateLimiter(min_interval=0.2)
        limiter.execute(lambda: None)  # This marks completion
        limiter.reset()
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # Should be nearly instant after reset

    def test_thread_safety(self):
        """Rate limiter should be thread-safe with execute."""
        limiter = RateLimiter(min_interval=0.1)
        results = []

        def worker():
            limiter.execute(lambda: results.append(1))

        threads = [threading.Thread(target=worker) for _ in range(5)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.monotonic() - start

        assert len(results) == 5
        # 5 calls with 0.1s interval should take at least 0.4s
        assert total_time >= 0.35


class TestGetRateLimiter:
    """Tests for get_rate_limiter function."""

    def test_returns_same_instance_for_same_key(self):
        """Should return same limiter for same API key."""
        limiter1 = get_rate_limiter("test_key_1")
        limiter2 = get_rate_limiter("test_key_1")
        assert limiter1 is limiter2

    def test_returns_different_instance_for_different_key(self):
        """Should return different limiter for different API key."""
        limiter1 = get_rate_limiter("test_key_a")
        limiter2 = get_rate_limiter("test_key_b")
        assert limiter1 is not limiter2

    def test_with_key_uses_1s_interval(self):
        """With API key, should use 1 second interval."""
        limiter = get_rate_limiter("some_api_key")
        assert limiter.min_interval == 1.0

    def test_without_key_uses_3s_interval(self):
        """Without API key, should use 3 second interval."""
        limiter = get_rate_limiter(None)
        assert limiter.min_interval == 3.0
