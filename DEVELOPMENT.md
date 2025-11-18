# راهنمای توسعه — Multi-Agent Trading Bot

این سند راهنمای کامل راه‌اندازی محیط توسعه، ساختار پروژه و workflow توسعه را ارائه می‌دهد.

## فهرست

1. [پیش‌نیازها](#پیشنیازها)
2. [راه‌اندازی اولیه](#راهاندازی-اولیه)
3. [ساختار پروژه](#ساختار-پروژه)
4. [اجرای محیط توسعه](#اجرای-محیط-توسعه)
5. [Development Workflow](#development-workflow)
6. [استانداردهای کد](#استانداردهای-کد)
7. [Debugging](#debugging)
8. [نکات عملی](#نکات-عملی)

---

## پیش‌نیازها

### نرم‌افزارهای مورد نیاز

#### 1. Docker & Docker Compose

```bash
# بررسی نسخه Docker
docker --version  # حداقل 20.10+
docker-compose --version  # حداقل 1.29+
```

**نصب** (اگر ندارید):
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux (Ubuntu/Debian)**:
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```

#### 2. Python 3.10+

```bash
python --version  # یا python3 --version
```

**نصب**:
- **Windows**: [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python@3.10`
- **Linux**: `sudo apt install python3.10 python3.10-venv`

#### 3. Git

```bash
git --version
```

#### 4. ابزارهای اختیاری (پیشنهادی)

- **Visual Studio Code** با extensions:
  - Python
  - Docker
  - YAML
  - GitLens
- **Postman** یا **Insomnia** برای تست APIها
- **Redis CLI**: `brew install redis` (macOS) یا `sudo apt install redis-tools` (Linux)
- **PostgreSQL Client**: `brew install postgresql` یا `sudo apt install postgresql-client`

---

## راه‌اندازی اولیه

### 1. Clone کردن Repository

```bash
git clone https://github.com/your-org/multi-agent.git
cd multi-agent
```

### 2. ایجاد محیط مجازی Python (اختیاری برای local development)

```bash
# ایجاد venv
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# نصب dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### 3. تنظیم Environment Variables

```bash
# کپی کردن template
cp .env.example .env

# ویرایش .env و مقادیر را تنظیم کنید
# حداقل موارد زیر را تنظیم کنید:
# - LLM_API_KEY
# - تمام پسوردها را تغییر دهید
```

**مثال `.env` برای development**:

```env
REDIS_PASSWORD=dev_redis_pass
POSTGRES_PASSWORD=dev_pg_pass
RABBITMQ_PASSWORD=dev_rmq_pass

JWT_SECRET=dev-jwt-secret-NOT-FOR-PRODUCTION
HMAC_SECRET=dev-hmac-secret-NOT-FOR-PRODUCTION

LLM_PROVIDER=openai
LLM_API_KEY=sk-your-actual-api-key-here
LLM_MODEL=gpt-4

LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### 4. ایجاد دایرکتوری‌های مورد نیاز

```bash
mkdir -p logs/{mcp,orchestrator,signal-agent,risk-agent,position-manager}
mkdir -p config/{grafana/dashboards,grafana/datasources}
mkdir -p freqtrade/user_data
```

### 5. راه‌اندازی سرویس‌های زیرساختی

```bash
# راه‌اندازی تنها سرویس‌های پایه (Redis, PostgreSQL, RabbitMQ)
docker-compose up -d redis postgres rabbitmq minio

# بررسی سلامت سرویس‌ها
docker-compose ps
docker-compose logs -f redis postgres rabbitmq
```

---

## ساختار پروژه

```
multi-agent/
├── .github/                    # GitHub Actions workflows
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
│
├── config/                     # فایل‌های تنظیمات
│   ├── prometheus.yml
│   ├── loki.yml
│   ├── promtail.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
│
├── docs/                       # مستندات
│   ├── README.md
│   ├── architecture.md
│   ├── api.md
│   ├── agents.md
│   ├── deployment.md
│   ├── security.md
│   ├── toon.md
│   ├── replay_engine.md
│   └── openapi.yaml
│
├── services/                   # سرویس‌های اصلی
│   ├── mcp-gateway/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py         # FastAPI app
│   │   │   ├── routes/
│   │   │   ├── models/
│   │   │   ├── auth/
│   │   │   └── utils/
│   │   └── tests/
│   │
│   ├── orchestrator/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── tasks/
│   │   │   ├── toon/           # TOON Layer
│   │   │   └── memory/         # MemorySvc
│   │   └── tests/
│   │
│   └── agents/
│       ├── Dockerfile.signal
│       ├── Dockerfile.risk
│       ├── Dockerfile.position
│       ├── requirements.txt
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── signal_agent.py
│       │   ├── risk_agent.py
│       │   └── position_manager.py
│       └── tests/
│
├── scripts/                    # اسکریپت‌های کمکی
│   ├── init-db.sql
│   ├── setup-dev.sh
│   ├── run-tests.sh
│   └── deploy.sh
│
├── tests/                      # Integration tests
│   ├── integration/
│   └── e2e/
│
├── logs/                       # لاگ‌ها (gitignored)
│
├── .env                        # Environment vars (gitignored)
├── .env.example                # Template
├── .gitignore
├── docker-compose.yml
├── requirements-dev.txt        # Development dependencies
├── DEVELOPMENT.md              # این فایل
├── TESTING.md
├── CONTRIBUTING.md
├── ROADMAP.md
└── README.md
```

---

## اجرای محیط توسعه

### سناریو 1: Full Stack (همه سرویس‌ها)

```bash
# راه‌اندازی تمام سرویس‌ها
docker-compose up --build

# یا در background:
docker-compose up -d --build

# مشاهده logs
docker-compose logs -f

# مشاهده logs یک سرویس خاص
docker-compose logs -f mcp-gateway
```

### سناریو 2: Development محلی با Docker برای dependencies

```bash
# فقط سرویس‌های زیرساختی
docker-compose up -d redis postgres rabbitmq minio

# اجرای MCP Gateway به صورت محلی
cd services/mcp-gateway
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# اجرای Orchestrator
cd services/orchestrator
python -m app.main

# اجرای Celery worker برای SignalAgent
cd services/agents
celery -A agents.signal_agent worker -Q signal_queue -l debug
```

### سناریو 3: تست با Freqtrade

```bash
# اجرا با Freqtrade local instance
docker-compose --profile with-freqtrade up -d

# بررسی Freqtrade UI
open http://localhost:8080
```

---

## Development Workflow

### 1. Feature Development

```bash
# ایجاد branch جدید
git checkout -b feature/my-new-feature

# Development...
# Test locally
docker-compose up --build

# Commit changes
git add .
git commit -m "feat: add my new feature"

# Push and create PR
git push origin feature/my-new-feature
```

### 2. Testing

```bash
# Unit tests
pytest services/mcp-gateway/tests/ -v

# Integration tests
pytest tests/integration/ -v

# با coverage
pytest --cov=services --cov-report=html
```

مشاهده [TESTING.md](./TESTING.md) برای جزئیات بیشتر.

### 3. Code Quality

```bash
# Linting
flake8 services/
pylint services/

# Formatting
black services/
isort services/

# Type checking
mypy services/
```

### 4. Pre-commit Hooks

```bash
# نصب pre-commit
pip install pre-commit
pre-commit install

# اجرا برای تمام فایل‌ها
pre-commit run --all-files
```

**.pre-commit-config.yaml**:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## استانداردهای کد

### Python Code Style

- **PEP 8** با حداکثر خط 100 کاراکتر
- **Type hints** برای تمام توابع
- **Docstrings** (Google style) برای کلاس‌ها و توابع public

**مثال**:

```python
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SignalAgent:
    """
    Agent برای تولید سیگنال‌های معاملاتی.

    این agent ترکیبی از قوانین ساده و LLM برای تصمیم‌گیری استفاده می‌کند.

    Attributes:
        mcp_client: کلاینت برای ارتباط با MCP Gateway
        llm_client: کلاینت برای ارتباط با LLM Provider
    """

    def __init__(self, mcp_url: str, llm_config: Dict[str, Any]):
        """
        Args:
            mcp_url: URL سرویس MCP Gateway
            llm_config: تنظیمات LLM provider
        """
        self.mcp_client = MCPClient(mcp_url)
        self.llm_client = LLMClient(**llm_config)

    async def evaluate_signal(
        self,
        pair: str,
        timeframe: str,
        candles: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        ارزیابی سیگنال برای یک جفت‌ارز.

        Args:
            pair: نماد جفت‌ارز (مثل BTC/USDT)
            timeframe: تایم‌فریم (15m, 1h, etc.)
            candles: لیست کندل‌ها

        Returns:
            Dict حاوی تصمیم یا None اگر سیگنالی نباشد

        Raises:
            ValueError: اگر ورودی‌ها نامعتبر باشند
            LLMError: اگر LLM query ناموفق باشد
        """
        if not candles:
            raise ValueError("Candles list cannot be empty")

        logger.info(f"Evaluating signal for {pair} on {timeframe}")

        # Logic...
        return decision
```

### Commit Message Convention

از **Conventional Commits** استفاده کنید:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: feature جدید
- `fix`: رفع bug
- `docs`: تغییرات مستندات
- `style`: formatting (بدون تغییر منطق)
- `refactor`: refactoring کد
- `test`: اضافه کردن/اصلاح تست‌ها
- `chore`: تغییرات build/config

**مثال‌ها**:

```bash
feat(signal-agent): add MACD crossover detection
fix(mcp-gateway): handle connection timeout errors
docs(architecture): add sequence diagram for order execution
test(risk-agent): add unit tests for position sizing
```

---

## Debugging

### 1. Debugging با VSCode

**.vscode/launch.json**:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: MCP Gateway",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/services/mcp-gateway",
      "env": {
        "REDIS_URL": "redis://:devpassword@localhost:6379/0",
        "LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### 2. Debugging Docker Containers

```bash
# اتصال به container
docker-compose exec mcp-gateway bash

# مشاهده logs real-time
docker-compose logs -f --tail=100 mcp-gateway

# بررسی environment variables
docker-compose exec mcp-gateway env

# اجرای Python REPL داخل container
docker-compose exec orchestrator python
```

### 3. Database Debugging

```bash
# اتصال به PostgreSQL
docker-compose exec postgres psql -U bot_user -d trading_bot

# اجرای query
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
```

```bash
# اتصال به Redis
docker-compose exec redis redis-cli -a devpassword

# بررسی keys
KEYS *

# مشاهده value
GET toon:BTC/USDT:15m
```

### 4. Network Debugging

```bash
# بررسی اتصال به MCP Gateway از داخل container
docker-compose exec orchestrator curl http://mcp-gateway:8000/api/v1/health

# بررسی connectivity
docker-compose exec orchestrator ping redis
```

---

## نکات عملی

### 1. Hot Reload

برای development سریع‌تر، از volume mount استفاده کنید:

```yaml
# در docker-compose.override.yml
services:
  mcp-gateway:
    volumes:
      - ./services/mcp-gateway/app:/app/app:ro
    command: uvicorn app.main:app --reload --host 0.0.0.0
```

### 2. Performance Profiling

```python
# با cProfile
python -m cProfile -o output.prof services/orchestrator/app/main.py

# تحلیل
python -m pstats output.prof
```

```python
# با line_profiler
@profile
def expensive_function():
    # ...
    pass

# اجرا
kernprof -l -v script.py
```

### 3. Memory Debugging

```python
# با memory_profiler
from memory_profiler import profile

@profile
def my_function():
    # ...
    pass
```

### 4. Environment-specific Settings

```python
# services/mcp-gateway/app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    redis_url: str
    postgres_url: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### 5. Makefile برای راحتی

**Makefile**:

```makefile
.PHONY: help build up down logs test lint format clean

help:  ## نمایش این راهنما
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build:  ## Build تمام سرویس‌ها
	docker-compose build

up:  ## راه‌اندازی تمام سرویس‌ها
	docker-compose up -d

down:  ## متوقف کردن تمام سرویس‌ها
	docker-compose down

logs:  ## مشاهده logs
	docker-compose logs -f

test:  ## اجرای تست‌ها
	pytest -v --cov

lint:  ## بررسی کیفیت کد
	flake8 services/
	pylint services/
	mypy services/

format:  ## فرمت کردن کد
	black services/
	isort services/

clean:  ## پاک کردن فایل‌های موقت
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
```

**استفاده**:

```bash
make help
make build
make up
make logs
make test
```

---

## منابع

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Freqtrade Documentation](https://www.freqtrade.io/en/stable/)

---

**سوالات یا مشکلات؟** یک issue در GitHub ایجاد کنید یا در Discussions پرسیده بگذارید.
