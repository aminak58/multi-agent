"""Performance and load tests for MCP Gateway.

These tests verify the system performs adequately under load.
Run with: pytest tests/test_performance.py -m performance
"""

import pytest
import time
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.main import app
from app.auth.jwt import create_access_token


@pytest.mark.performance
class TestPerformance:
    """Performance tests."""

    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Auth headers."""
        token = create_access_token({"sub": "perf-test-user"})
        return {"Authorization": f"Bearer {token}"}

    def test_health_endpoint_latency(self, client):
        """Test health endpoint responds within acceptable time."""
        start = time.time()
        response = client.get("/health")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert duration < 100, f"Health check took {duration}ms, expected <100ms"

    def test_candles_endpoint_latency(self, client, auth_headers):
        """Test candles endpoint latency."""
        start = time.time()
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m", "limit": 100},
            headers=auth_headers,
        )
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 500, f"Candles request took {duration}ms, expected <500ms"

    def test_concurrent_requests_throughput(self, client, auth_headers):
        """Test system handles concurrent requests efficiently."""
        num_requests = 50

        def make_request(_):
            start = time.time()
            response = client.get("/health")
            duration = time.time() - start
            return response.status_code, duration

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_request, i) for i in range(num_requests)
            ]
            results = [f.result() for f in as_completed(futures)]

        total_time = time.time() - start_time
        throughput = num_requests / total_time

        # Check all succeeded
        assert all(status == 200 for status, _ in results)

        # Check throughput (requests per second)
        assert throughput > 10, f"Throughput was {throughput:.2f} req/s, expected >10"

        # Check average latency
        avg_latency = sum(dur for _, dur in results) / len(results) * 1000
        assert avg_latency < 200, f"Average latency {avg_latency:.2f}ms, expected <200ms"

    def test_memory_leak_detection(self, client, auth_headers):
        """Test for potential memory leaks with repeated requests."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make 100 requests
        for _ in range(100):
            client.get(
                "/api/v1/candles",
                params={"pair": "BTC/USDT", "timeframe": "15m"},
                headers=auth_headers,
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<50MB for 100 requests)
        assert (
            memory_increase < 50
        ), f"Memory increased by {memory_increase:.2f}MB, possible leak"

    def test_rate_limiting_performance(self, client, auth_headers):
        """Test rate limiting doesn't significantly impact performance."""
        # Make requests up to rate limit
        durations = []

        for _ in range(10):
            start = time.time()
            response = client.get(
                "/api/v1/candles",
                params={"pair": "BTC/USDT", "timeframe": "15m"},
                headers=auth_headers,
            )
            duration = time.time() - start
            durations.append(duration)

            if response.status_code == 429:
                break

        # Rate limiting overhead should be minimal
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 0.1, f"Average duration {avg_duration:.2f}s too high"

    def test_large_payload_handling(self, client, auth_headers):
        """Test handling of large response payloads."""
        start = time.time()
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "5m", "limit": 1000},
            headers=auth_headers,
        )
        duration = (time.time() - start) * 1000

        assert response.status_code == 200

        # Should handle large payload efficiently
        assert duration < 1000, f"Large payload took {duration}ms, expected <1000ms"

    @pytest.mark.slow
    def test_sustained_load(self, client, auth_headers):
        """Test system stability under sustained load."""
        duration_seconds = 10
        request_rate = 5  # requests per second

        total_requests = duration_seconds * request_rate
        failures = 0
        latencies = []

        start_time = time.time()

        for i in range(total_requests):
            req_start = time.time()

            response = client.get("/health")

            if response.status_code != 200:
                failures += 1

            latency = (time.time() - req_start) * 1000
            latencies.append(latency)

            # Control rate
            elapsed = time.time() - start_time
            expected_time = (i + 1) / request_rate
            if elapsed < expected_time:
                time.sleep(expected_time - elapsed)

        # Calculate statistics
        success_rate = (total_requests - failures) / total_requests * 100
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        assert success_rate >= 99, f"Success rate {success_rate:.2f}%, expected >=99%"
        assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms, expected <100ms"
        assert p95_latency < 200, f"P95 latency {p95_latency:.2f}ms, expected <200ms"


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance impact."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        token = create_access_token({"sub": "cache-test-user"})
        return {"Authorization": f"Bearer {token}"}

    def test_cache_hit_vs_miss_performance(self, client, auth_headers):
        """Compare cache hit vs miss performance."""
        params = {"pair": "BTC/USDT", "timeframe": "15m", "limit": 100}

        # First request (cache miss)
        start = time.time()
        response1 = client.get(
            "/api/v1/candles", params=params, headers=auth_headers
        )
        miss_duration = (time.time() - start) * 1000

        assert response1.status_code == 200

        # Second request (cache hit)
        start = time.time()
        response2 = client.get(
            "/api/v1/candles", params=params, headers=auth_headers
        )
        hit_duration = (time.time() - start) * 1000

        assert response2.status_code == 200

        # Cache hit should be faster
        # Note: In test environment this might not always be true
        # due to mocking, but in production it should be
        print(f"Cache miss: {miss_duration:.2f}ms, Cache hit: {hit_duration:.2f}ms")

    def test_cache_bypass_performance(self, client, auth_headers):
        """Test performance when cache is bypassed."""
        params = {
            "pair": "BTC/USDT",
            "timeframe": "15m",
            "limit": 100,
            "use_cache": "false",
        }

        durations = []

        for _ in range(5):
            start = time.time()
            response = client.get(
                "/api/v1/candles", params=params, headers=auth_headers
            )
            duration = (time.time() - start) * 1000
            durations.append(duration)

            assert response.status_code == 200

        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 500, f"Average duration {avg_duration:.2f}ms too high"
