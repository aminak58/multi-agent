# Testing Guide - MCP Gateway

این سند راهنمای کامل testing برای MCP Gateway را ارائه می‌دهد.

## فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [راه‌اندازی محیط تست](#راهاندازی-محیط-تست)
3. [اجرای تست‌ها](#اجرای-تستها)
4. [انواع تست](#انواع-تست)
5. [Coverage](#coverage)
6. [CI/CD Integration](#cicd-integration)
7. [نوشتن تست جدید](#نوشتن-تست-جدید)

---

## نگاه کلی

Test Suite شامل:

- ✅ **Unit Tests**: تست اجزای مجزا (auth, clients, utils)
- ✅ **Integration Tests**: تست یکپارچگی سرویس‌ها
- ✅ **End-to-End Tests**: تست جریان‌های کامل API
- ✅ **Performance Tests**: تست عملکرد و کارایی
- ✅ **Load Tests**: تست تحت بار

### Test Statistics

- **Total Tests**: 100+
- **Coverage Target**: >80%
- **Test Duration**: ~30 seconds (fast), ~2 minutes (all)
- **Test Files**: 10+

---

## راه‌اندازی محیط تست

### نصب Dependencies

```bash
cd services/mcp-gateway

# با Make
make install-dev

# یا دستی
python -m venv venv
source venv/bin/activate  # یا venv\Scripts\activate در Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### تنظیم Environment Variables

```bash
# کپی کردن .env.example
cp ../../.env.example ../../.env

# ویرایش برای test environment
# تنظیم Redis, PostgreSQL برای testing
```

---

## اجرای تست‌ها

### با Make (توصیه می‌شود)

```bash
# تمام تست‌ها با coverage
make test

# فقط unit tests
make test-unit

# فقط integration tests
make test-integration

# فقط performance tests
make test-performance

# تست‌های سریع (بدون slow tests)
make test-fast

# تست در Docker
make test-docker
```

### با Pytest مستقیم

```bash
# تمام تست‌ها
pytest -v

# با coverage
pytest --cov=app --cov-report=html

# فقط unit tests
pytest tests/ -m "not integration and not performance"

# فقط integration tests
pytest tests/ -m integration

# فقط performance tests
pytest tests/ -m performance

# تست خاص
pytest tests/test_auth.py -v

# تست یک کلاس
pytest tests/test_auth.py::TestJWT -v

# تست یک متد
pytest tests/test_auth.py::TestJWT::test_create_access_token -v
```

### با Scripts

```bash
# اجرا با script
./scripts/run_tests.sh all true

# بدون coverage
./scripts/run_tests.sh unit false

# تست در Docker
./scripts/test_docker.sh
```

---

## انواع تست

### 1. Unit Tests

تست اجزای مجزا بدون dependency به سرویس‌های خارجی.

**فایل‌ها:**
- `test_auth.py` - JWT و HMAC authentication
- `test_config.py` - Configuration management
- `test_cache.py` - Redis cache utilities
- `test_logger.py` - Logging utilities
- `test_freqtrade_client.py` - Freqtrade client

**اجرا:**
```bash
pytest tests/ -m "not integration and not performance" -v
```

**مثال:**
```python
# tests/test_auth.py
def test_create_access_token():
    """Test JWT token creation."""
    payload = {"sub": "test-user"}
    token = create_access_token(payload)

    assert isinstance(token, str)
    assert len(token) > 0
```

### 2. Integration Tests

تست یکپارچگی بین اجزای مختلف.

**فایل‌ها:**
- `test_integration.py` - End-to-end workflows
- `test_routes.py` - API endpoint integration

**اجرا:**
```bash
pytest tests/ -m integration -v
```

**مثال:**
```python
@pytest.mark.integration
def test_complete_order_flow(client, auth_headers):
    """Test dry-run -> validation -> execution flow."""
    # 1. Dry-run
    dry_response = client.post("/api/v1/orders/dry-run", ...)
    assert dry_response.status_code == 200

    # 2. Execute
    exec_response = client.post("/api/v1/orders", ...)
    # ... assertions
```

### 3. End-to-End Tests

تست کامل از ابتدا تا انتها.

**شامل:**
- Authentication flow
- Complete order lifecycle
- Caching behavior
- Error handling cascade

**اجرا:**
```bash
pytest tests/test_integration.py::TestEndToEndFlow -v
```

### 4. Performance Tests

تست عملکرد و latency.

**فایل‌ها:**
- `test_performance.py` - Performance metrics

**اجرا:**
```bash
pytest tests/ -m performance -v
```

**تست‌های شامل:**
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Concurrent request handling
- Memory leak detection
- Cache performance

**مثال:**
```python
@pytest.mark.performance
def test_health_endpoint_latency(client):
    """Test health endpoint latency."""
    start = time.time()
    response = client.get("/health")
    duration = (time.time() - start) * 1000

    assert response.status_code == 200
    assert duration < 100  # <100ms
```

### 5. Load Tests

تست تحت بار و sustained load.

**اجرا:**
```bash
pytest tests/test_performance.py::TestPerformance::test_sustained_load -v
```

**Metrics:**
- Success rate >= 99%
- Average latency < 100ms
- P95 latency < 200ms

---

## Coverage

### اجرای Coverage

```bash
# با Make
make coverage-report

# با Pytest
pytest --cov=app --cov-report=term-missing --cov-report=html

# فقط نمایش
pytest --cov=app --cov-report=term
```

### مشاهده HTML Report

```bash
# تولید HTML report
make coverage-html

# باز کردن در browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Targets

- **Overall**: >80%
- **Critical modules** (auth, clients): >90%
- **Routes**: >85%
- **Utils**: >75%

### Coverage Configuration

در `pytest.ini`:
```ini
[pytest]
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd services/mcp-gateway
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd services/mcp-gateway
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd services/mcp-gateway
make test-fast
```

---

## نوشتن تست جدید

### ساختار تست

```python
"""Test module description."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.module import function_to_test


@pytest.mark.unit  # یا integration, performance
class TestFeatureName:
    """Test suite for FeatureName."""

    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return {"key": "value"}

    def test_successful_case(self, setup_data):
        """Test successful case.

        Given: Initial condition
        When: Action performed
        Then: Expected result
        """
        # Arrange
        input_data = setup_data

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == expected_value

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            function_to_test(invalid_input)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked dependency."""
    with patch('app.client.external_api') as mock_api:
        mock_api.get.return_value = {"data": "value"}

        result = await function_using_api()

        assert result == expected
        mock_api.get.assert_called_once()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("buy", OrderSide.BUY),
    ("sell", OrderSide.SELL),
])
def test_multiple_cases(input, expected):
    """Test multiple cases."""
    result = parse_side(input)
    assert result == expected
```

### Test Utilities

استفاده از helpers در `tests/utils.py`:

```python
from tests.utils import (
    generate_candles,
    generate_position,
    generate_order_request,
    assert_candle_valid,
)

def test_with_utility():
    """Test using utilities."""
    candles = generate_candles(count=100)
    assert len(candles) == 100

    for candle in candles:
        assert_candle_valid(candle.dict())
```

---

## Best Practices

### 1. Test Naming

```python
# ✅ خوب
def test_create_order_with_valid_data_returns_success()

# ❌ بد
def test1()
def test_order()
```

### 2. AAA Pattern

```python
def test_function():
    # Arrange - setup
    data = create_test_data()

    # Act - execute
    result = function_under_test(data)

    # Assert - verify
    assert result == expected
```

### 3. One Assertion Per Test (ترجیحاً)

```python
# ✅ بهتر
def test_user_creation_sets_id():
    user = create_user()
    assert user.id is not None

def test_user_creation_sets_timestamp():
    user = create_user()
    assert user.created_at is not None

# ⚠️ قابل قبول
def test_user_creation():
    user = create_user()
    assert user.id is not None
    assert user.created_at is not None
```

### 4. Test Independence

```python
# ✅ هر تست مستقل است
def test_a():
    setup_a()
    # test...
    cleanup_a()

def test_b():
    setup_b()
    # test...
    cleanup_b()

# ❌ تست‌ها به هم وابسته‌اند
def test_a():
    global_state = "value"

def test_b():
    # uses global_state from test_a
```

### 5. Clear Error Messages

```python
# ✅ خوب
assert len(candles) == 100, f"Expected 100 candles, got {len(candles)}"

# ❌ بد
assert len(candles) == 100
```

---

## Troubleshooting

### تست‌ها fail می‌شوند

```bash
# بررسی dependencies
pip install -r requirements.txt

# پاک کردن cache
make clean

# اجرای مجدد
make test
```

### Coverage پایین

```bash
# مشاهده فایل‌های بدون coverage
pytest --cov=app --cov-report=term-missing

# تست فقط یک ماژول
pytest --cov=app.auth tests/test_auth.py -v
```

### Performance tests کند هستند

```bash
# اجرای بدون performance tests
make test-fast

# یا
pytest tests/ -m "not performance and not slow"
```

### Redis/PostgreSQL errors

```bash
# راه‌اندازی services با Docker
docker-compose up -d redis postgres

# بررسی اتصال
redis-cli -h localhost -p 6379 ping
psql -h localhost -U bot_user -d trading_bot
```

---

## منابع

- **Pytest Documentation**: https://docs.pytest.org/
- **Pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Coverage.py**: https://coverage.readthedocs.io/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/

---

**Maintainer**: Multi-Agent Team
**Last Updated**: 2025-11-18
**Version**: 1.0
