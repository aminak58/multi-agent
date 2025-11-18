# MCP Gateway

**Market Data & Order Execution Gateway** for Multi-Agent Trading Bot

## نگاه کلی

MCP Gateway یک API Gateway با امنیت بالا است که رابط بین Multi-Agent Trading System و Freqtrade فراهم می‌کند. این gateway مسئول:

- ✅ دریافت داده‌های بازار (OHLCV candles)
- ✅ مدیریت پوزیشن‌های باز
- ✅ اجرای سفارشات (با قابلیت dry-run)
- ✅ احراز هویت و امنیت (JWT + HMAC)
- ✅ Rate limiting و caching
- ✅ Monitoring و metrics

## ویژگی‌ها

### امنیت
- **JWT Authentication**: احراز هویت کاربران
- **HMAC Signature**: اعتبارسنجی تراکنش‌های حساس
- **Rate Limiting**: محافظت در برابر سوء استفاده
- **Input Validation**: Pydantic schemas

### Performance
- **Redis Caching**: کاهش latency برای داده‌های تکراری
- **Async I/O**: پشتیبانی از همزمانی بالا
- **Connection Pooling**: مدیریت بهینه اتصالات

### Observability
- **Prometheus Metrics**: metrics زمان واقعی
- **Structured Logging**: JSON logs
- **Health Checks**: monitoring سلامت سرویس‌ها

## معماری

```
┌─────────────────┐
│  Agents/Clients │
└────────┬────────┘
         │ JWT + HMAC
         ▼
┌─────────────────────────┐
│     MCP Gateway         │
│  ┌─────────────────┐    │
│  │  FastAPI Routes │    │
│  └────────┬────────┘    │
│           │             │
│  ┌────────┴────────┐    │
│  │  Auth Middleware│    │
│  └────────┬────────┘    │
│           │             │
│  ┌────────┴─────────┐   │
│  │ Freqtrade Client │   │
│  └────────┬─────────┘   │
└───────────┼─────────────┘
            │
            ▼
    ┌───────────────┐
    │  Freqtrade    │
    │  (Exchange)   │
    └───────────────┘
```

## Installation

### با Docker (توصیه می‌شود)

```bash
# از root directory پروژه
docker-compose up -d mcp-gateway
```

### Development محلی

```bash
cd services/mcp-gateway

# ایجاد virtual environment
python -m venv venv
source venv/bin/activate  # یا venv\Scripts\activate در Windows

# نصب dependencies
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
cp ../../.env.example ../../.env
# ویرایش .env

# اجرای migrations
alembic upgrade head

# اجرای server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

تمام تنظیمات از طریق environment variables:

```bash
# Security
JWT_SECRET=your-secret-key
HMAC_SECRET=your-hmac-secret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=trading_bot

# Freqtrade
FREQTRADE_URL=http://localhost:8080
FREQTRADE_USERNAME=your-username
FREQTRADE_PASSWORD=your-password

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## API Documentation

### Authentication

همه endpoints نیاز به JWT token دارند:

```bash
# دریافت token (در production از یک auth service استفاده کنید)
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'

# استفاده از token
curl http://localhost:8000/api/v1/candles?pair=BTC/USDT&timeframe=15m \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Endpoints

#### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:00:00Z",
  "version": "0.1.0",
  "services": {
    "redis": "healthy",
    "freqtrade": "healthy"
  }
}
```

#### Get Candles
```bash
GET /api/v1/candles
```

**Query Parameters:**
- `pair` (required): Trading pair (e.g., BTC/USDT)
- `timeframe` (required): Timeframe (5m, 15m, 1h, 4h, 1d)
- `limit` (optional): Number of candles (default: 500, max: 1000)
- `use_cache` (optional): Use cached data (default: true)

**Response:**
```json
{
  "pair": "BTC/USDT",
  "timeframe": "15m",
  "count": 100,
  "candles": [
    {
      "timestamp": 1700000000,
      "open": 50000.0,
      "high": 51000.0,
      "low": 49000.0,
      "close": 50500.0,
      "volume": 100.0
    }
  ]
}
```

#### Get Open Positions
```bash
GET /api/v1/positions/open
```

**Response:**
```json
{
  "total_count": 2,
  "positions": [
    {
      "pair": "BTC/USDT",
      "side": "buy",
      "amount": 0.01,
      "entry_price": 50000.0,
      "current_price": 51000.0,
      "unrealized_pnl": 10.0,
      "unrealized_pnl_pct": 2.0,
      "stop_loss": 49000.0,
      "take_profit": null,
      "open_date": "2025-11-18T10:00:00Z"
    }
  ]
}
```

#### Dry-Run Order
```bash
POST /api/v1/orders/dry-run
```

**Request Body:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "signal-agent",
  "pair": "BTC/USDT",
  "side": "buy",
  "amount": 0.001,
  "order_type": "market"
}
```

**Response:**
```json
{
  "valid": true,
  "estimated_cost": 1000.0,
  "estimated_fee": 1.0,
  "warnings": [],
  "errors": []
}
```

#### Create Order
```bash
POST /api/v1/orders
```

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>`
- `X-Signature: <HMAC_SIGNATURE>`

**Request Body:** (همانند dry-run)

**Response:**
```json
{
  "order_id": "abc123",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "pair": "BTC/USDT",
  "side": "buy",
  "amount": 0.001,
  "filled_amount": 0.0,
  "timestamp": "2025-11-18T10:00:00Z",
  "message": "Order submitted successfully"
}
```

### HMAC Signature

برای endpoints حساس (مانند `/orders`), باید HMAC signature محاسبه و ارسال کنید:

```python
import hmac
import hashlib
import json

secret = "your-hmac-secret"
body = json.dumps(order_data)
signature = hmac.new(
    secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "X-Signature": signature
}
```

## Testing

```bash
# اجرای تمام تست‌ها
pytest

# با coverage
pytest --cov=app --cov-report=html

# فقط unit tests
pytest tests/ -m unit

# فقط integration tests
pytest tests/ -m integration
```

## Monitoring

### Prometheus Metrics

Metrics در `/metrics` در دسترس است:

```bash
curl http://localhost:8000/metrics
```

**Metrics کلیدی:**
- `http_requests_total`: تعداد کل requests
- `http_request_duration_seconds`: latency requests
- `http_requests_in_progress`: requests در حال اجرا

### Logs

Logs به صورت JSON در stdout:

```json
{
  "timestamp": "2025-11-18T10:00:00Z",
  "level": "INFO",
  "name": "app.routes.candles",
  "message": "Candles requested",
  "pair": "BTC/USDT",
  "timeframe": "15m",
  "user": "test-user"
}
```

## Troubleshooting

### Connection به Redis ناموفق

```bash
# بررسی Redis
docker-compose ps redis

# تست اتصال
redis-cli -h localhost -p 6379 -a your-password ping
```

### Connection به Freqtrade ناموفق

```bash
# بررسی Freqtrade
curl http://localhost:8080/api/v1/ping

# بررسی credentials
curl -u username:password http://localhost:8080/api/v1/ping
```

### Performance کند

- ✅ فعال کردن Redis caching
- ✅ افزایش `REDIS_TTL`
- ✅ بررسی latency شبکه به Freqtrade
- ✅ افزایش connection pool size

## Development

### Structure

```
services/mcp-gateway/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── routes/              # API endpoints
│   ├── models/              # Pydantic schemas
│   ├── auth/                # JWT & HMAC
│   ├── clients/             # Freqtrade client
│   ├── middleware/          # Rate limiting
│   └── utils/               # Logging, cache
├── tests/
├── alembic/                 # Database migrations
├── Dockerfile
├── requirements.txt
└── README.md
```

### Adding New Endpoint

1. ایجاد schema در `models/schemas.py`
2. ایجاد route در `routes/`
3. ثبت router در `main.py`
4. نوشتن tests در `tests/`
5. Update این README

## Contributing

مشاهده [CONTRIBUTING.md](../../CONTRIBUTING.md) برای جزئیات.

## License

[بر اساس license پروژه]

---

**Maintainer**: Multi-Agent Team
**Version**: 0.1.0
**Last Updated**: 2025-11-18
