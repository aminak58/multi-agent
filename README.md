# Multi-Agent Hybrid Trading Bot

<div align="center">

**ربات معاملاتی چندعاملی هوشمند برای Freqtrade**
*ترکیب قواعد کلاسیک + LLM + TOON برای تصمیم‌گیری تطبیقی*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[مستندات](docs/) | [نقشه راه](ROADMAP.md) | [راهنمای توسعه](DEVELOPMENT.md) | [API Spec](docs/openapi.yaml)

</div>

---

## 🎯 نگاه کلی

این پروژه یک **ربات معاملاتی چندعاملی** است که با ترکیب قدرت **قواعد تحلیل تکنیکال کلاسیک** و **هوش مصنوعی (LLM)**، تصمیمات معاملاتی هوشمند و قابل توضیح ارائه می‌دهد.

### چرا این پروژه؟

- ✅ **Hybrid Approach**: ترکیب قواعد ساده (سریع، ارزان) با LLM (هوشمند، انعطاف‌پذیر)
- ✅ **Explainable AI**: تمام تصمیمات با دلیل (reasoning) ثبت می‌شوند
- ✅ **Reproducible Backtest**: با LLM Replay Engine، بک‌تست‌های deterministic
- ✅ **Production-Ready**: معماری مقیاس‌پذیر، امن و قابل نگهداری
- ✅ **Open Source**: شفاف، قابل تست و قابل سفارشی‌سازی

---

## 🚀 ویژگی‌های کلیدی

### معماری Multi-Agent

```
┌─────────────────┐
│  Freqtrade      │ ← اتصال امن از طریق MCP Gateway
└────────┬────────┘
         │
    ┌────▼────┐
    │   MCP   │ ← REST API با JWT + HMAC
    └────┬────┘
         │
    ┌────▼────────┐
    │ Orchestrator│ ← مدیریت جریان و زمان‌بندی
    └──┬──┬───┬──┘
       │  │   │
   ┌───▼──▼───▼────┐
   │   Agents:      │
   │ - SignalAgent  │ ← تولید سیگنال (Rules + LLM)
   │ - RiskAgent    │ ← محاسبه Position Size
   │ - PositionMgr  │ ← اجرای سفارش
   └────────────────┘
```

[مشاهده نمودارهای کامل معماری →](docs/architecture.md)

### TOON (Tokenized Observational Notation)

روشی برای **فشرده‌سازی داده‌های زمانی** به فرمتی کارآمد برای LLM:

- کاهش هزینه و latency
- Deterministic encoding برای replay
- قابلیت cache و hash

[جزئیات TOON →](docs/toon.md)

### LLM Replay Engine

برای **بک‌تست قابل تکرار**:

- ضبط تمام پرامپت‌ها و پاسخ‌های LLM
- بازپخش deterministic در backtest
- Fallback strategies (nearest match, surrogate model)

[جزئیات Replay Engine →](docs/replay_engine.md)

---

## 📦 شروع سریع

### پیش‌نیازها

- **Docker** 20.10+ و **Docker Compose** 1.29+
- **Python** 3.10+ (برای development محلی)
- **Git**
- کلید API از OpenAI/Anthropic (برای LLM)

### راه‌اندازی با 3 مرحله

```bash
# 1. Clone repository
git clone https://github.com/your-org/multi-agent.git
cd multi-agent

# 2. تنظیم environment variables
cp .env.example .env
# ویرایش .env و LLM_API_KEY را تنظیم کنید

# 3. اجرا
docker-compose up --build
```

**سرویس‌های در دسترس**:

- **MCP Gateway**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **RabbitMQ**: http://localhost:15672 (bot_user/devpassword)

### تست سریع

```bash
# بررسی سلامت MCP Gateway
curl http://localhost:8000/api/v1/health

# دریافت کندل‌ها
curl "http://localhost:8000/api/v1/candles?pair=BTC/USDT&tf=15m&n=10"
```

[راهنمای کامل راه‌اندازی →](DEVELOPMENT.md)

---

## 📚 مستندات

### مستندات اصلی

| سند | توضیح |
|-----|-------|
| [**ROADMAP.md**](ROADMAP.md) | نقشه راه پیاده‌سازی فازبندی‌شده (12 هفته) |
| [**DEVELOPMENT.md**](DEVELOPMENT.md) | راهنمای توسعه و setup محیط |
| [**TESTING.md**](TESTING.md) | استراتژی testing و best practices |
| [**CONTRIBUTING.md**](CONTRIBUTING.md) | راهنمای مشارکت در پروژه |

### مستندات فنی

| سند | توضیح |
|-----|-------|
| [**docs/architecture.md**](docs/architecture.md) | معماری کامل با نمودارها |
| [**docs/api.md**](docs/api.md) | توضیحات API و examples |
| [**docs/openapi.yaml**](docs/openapi.yaml) | OpenAPI 3.0 Specification |
| [**docs/agents.md**](docs/agents.md) | شرح agentها و قراردادها |
| [**docs/toon.md**](docs/toon.md) | طراحی TOON Layer |
| [**docs/replay_engine.md**](docs/replay_engine.md) | LLM Replay برای backtest |
| [**docs/security.md**](docs/security.md) | امنیت و authentication |
| [**docs/deployment.md**](docs/deployment.md) | راه‌اندازی production |

---

## 🏗️ ساختار پروژه

```
multi-agent/
├── services/               # سرویس‌های اصلی
│   ├── mcp-gateway/       # MCP Gateway (FastAPI)
│   ├── orchestrator/      # Orchestrator + TOON Layer
│   └── agents/            # SignalAgent, RiskAgent, PositionManager
├── docs/                  # مستندات فنی
├── config/                # تنظیمات (Prometheus, Grafana, etc.)
├── scripts/               # اسکریپت‌های کمکی
├── tests/                 # Integration & E2E tests
├── docker-compose.yml     # راه‌اندازی کامل
├── .env.example           # Template متغیرهای محیطی
├── ROADMAP.md             # نقشه راه 12 هفته‌ای
└── README.md              # این فایل
```

---

## 🛣️ نقشه راه

### فازهای پیاده‌سازی

| فاز | زمان | وضعیت | توضیح |
|-----|------|--------|-------|
| **فاز 0** | هفته 1 | ✅ | پایه‌گذاری، CI/CD، مستندات |
| **فاز 1** | هفته 2-3 | 🔄 | MCP Gateway + Database |
| **فاز 2** | هفته 4-5 | ⏳ | Orchestrator + Agents |
| **فاز 3** | هفته 6-7 | ⏳ | LLM Integration + TOON |
| **فاز 4** | هفته 8-9 | ⏳ | Replay Engine + Backtest |
| **فاز 5** | هفته 10-11 | ⏳ | Production Hardening |
| **فاز 6** | هفته 12+ | ⏳ | Advanced Features |

**Milestones**:
- ✅ **M0**: Foundation Complete
- 🔄 **M1**: MVP Core (End of Week 3)
- ⏳ **M2**: Multi-Agent System (End of Week 5)
- ⏳ **M3**: LLM Integration (End of Week 7)
- ⏳ **M4**: Backtest Ready (End of Week 9)
- ⏳ **M5**: Production Ready (End of Week 11)

[مشاهده نقشه راه کامل →](ROADMAP.md)

---

## 🤝 مشارکت

ما به کمک شما نیاز داریم! مشارکت‌ها خوش‌آمد هستند.

### چگونه مشارکت کنیم؟

1. **Fork** کردن repository
2. ایجاد **branch** جدید (`git checkout -b feature/amazing-feature`)
3. **Commit** تغییرات (`git commit -m 'feat: add amazing feature'`)
4. **Push** به branch (`git push origin feature/amazing-feature`)
5. ایجاد **Pull Request**

[راهنمای کامل مشارکت →](CONTRIBUTING.md)

### انواع مشارکت

- 🐛 گزارش باگ
- 💡 پیشنهاد ویژگی جدید
- 📝 بهبود مستندات
- 🧪 نوشتن تست
- 💻 پیاده‌سازی features
- 🎨 بهبود UI/UX

---

## 📊 وضعیت پروژه

### آمار فعلی

- **Code Coverage**: - (در حال توسعه)
- **Open Issues**: [مشاهده →](https://github.com/your-org/multi-agent/issues)
- **Contributors**: [مشاهده →](https://github.com/your-org/multi-agent/graphs/contributors)

### تکنولوژی‌های استفاده‌شده

**Backend**:
- FastAPI (REST API)
- Celery (Task Queue)
- PostgreSQL (Database)
- Redis (Cache & State)
- RabbitMQ (Message Queue)

**AI/ML**:
- OpenAI/Anthropic (LLM)
- Pandas/NumPy (Data Processing)
- TOON (Custom Encoding)

**Infrastructure**:
- Docker & Docker Compose
- Prometheus + Grafana (Monitoring)
- Loki + Promtail (Logging)
- GitHub Actions (CI/CD)

---

## ⚠️ Disclaimer

**این پروژه صرفاً برای اهداف آموزشی و تحقیقاتی است.**

- معاملات ارزهای دیجیتال ریسک بالایی دارند
- از این ربات در محیط واقعی بدون تست کامل استفاده نکنید
- مسئولیت سود/ضرر بر عهده شما است
- همیشه از paper trading برای شروع استفاده کنید

---

## 📄 مجوز

این پروژه تحت مجوز **MIT** منتشر شده است - مشاهده فایل [LICENSE](LICENSE) برای جزئیات.

---

## 📞 ارتباط و پشتیبانی

- **Issues**: [GitHub Issues](https://github.com/your-org/multi-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/multi-agent/discussions)
- **Email**: support@your-domain.com (در صورت وجود)

---

## 🙏 قدردانی

این پروژه از پروژه‌های زیر الهام گرفته و استفاده کرده است:

- [Freqtrade](https://www.freqtrade.io/) - Trading bot framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Celery](https://docs.celeryq.dev/) - Distributed task queue

---

<div align="center">

**ساخته شده با ❤️ توسط تیم Multi-Agent**

⭐ اگر این پروژه را مفید یافتید، یک ستاره بدهید!

</div>
