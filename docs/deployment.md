# استقرار و اجرای محلی (MVP)

این فایل مراحل سریع راه‌اندازی محلی برای تست و توسعه را توضیح می‌دهد.

## پیش‌نیازها
- نصب Docker و Docker Compose
- Python 3.10+ برای اجرای اسکریپت‌ها (اختیاری)
- `git` و `gh` برای عملیات ریپازیتوری

## نمونهٔ `docker-compose.yml` برای MVP
مثال خلاصه (قرار داده شده در ریشه پروژه یا `deploy/`):

```yaml
version: '3.8'
services:
  redis:
    image: redis:7
    ports: ["6379:6379"]
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: example
    ports: ["5432:5432"]
  mcp:
    build: ./mcp
    ports: ["8000:8000"]
    depends_on: [redis, postgres]
  signal_agent:
    build: ./agents/signal
    depends_on: [mcp]
```

## اجرای محلی (دایرکتوری پروژه)
```powershell
cd C:\FreqtradeProjects\multi-agent
docker-compose up --build
```

## تست سریع end-to-end (paper)
1. راه‌اندازی `docker-compose` و اطمینان از سلامت سرویس‌ها.
2. اجرای یک سناریوی paper-trade در Freqtrade (یا ارسال کندل‌های تستی به MCP).
3. مانیتور کردن لاگ‌ها و داشبوردها.

## نکات production
- استفاده از Kubernetes برای مقیاس‌پذیری و HPA
- secrets در Vault یا AWS Secrets Manager
- observability: Prometheus/Grafana + ELK / Loki
