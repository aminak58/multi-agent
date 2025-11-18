# Orchestrator Service

**Event-driven coordinator** for Multi-Agent Trading System

## نگاه کلی

Orchestrator مسئول هماهنگی بین agents مختلف است:

- 📥 دریافت webhook updates (candle data)
- 🔀 Routing tasks به agents مناسب
- 📊 State management
- ⚡ Event-driven architecture
- 🔄 Retry & error handling

## Architecture

```
Webhook → Orchestrator → RabbitMQ → Agents
                ↓
            Redis (State)
```

## Components

- **FastAPI**: REST API endpoints
- **Celery**: Async task execution
- **RabbitMQ**: Message broker
- **Redis**: State & caching

## Status

🚧 **Under Development** - Phase 2

---

**Version**: 0.1.0
**Phase**: 2 - Multi-Agent System
