# نقشه راه پیاده‌سازی — Multi-Agent Trading Bot

این سند برنامه‌ریزی فازبندی‌شده و قابل اجرا برای تبدیل مستندات به یک سیستم کاملاً عملیاتی است.

## فهرست

1. [نگاه کلی](#نگاه-کلی)
2. [فاز 0: پایه‌گذاری](#فاز-0-پایهگذاری-هفته-1)
3. [فاز 1: MVP Core](#فاز-1-mvp-core-هفته-2-3)
4. [فاز 2: Multi-Agent System](#فاز-2-multi-agent-system-هفته-4-5)
5. [فاز 3: LLM Integration & TOON](#فاز-3-llm-integration--toon-هفته-6-7)
6. [فاز 4: Replay Engine & Backtest](#فاز-4-replay-engine--backtest-هفته-8-9)
7. [فاز 5: Production Hardening](#فاز-5-production-hardening-هفته-10-11)
8. [فاز 6: Advanced Features](#فاز-6-advanced-features-هفته-12)
9. [Milestones](#milestones)
10. [KPIs هر فاز](#kpis-هر-فاز)

---

## نگاه کلی

### اهداف کلی

✅ **MVP قابل استفاده در 6 هفته**  
✅ **Production-ready در 12 هفته**  
✅ **Architecture مقیاس‌پذیر و قابل نگهداری**  
✅ **Documentation کامل برای هر بخش**

### مبنای زمان‌بندی

- تیم: **1-2 developer** (full-time equivalent)
- Sprint: **2 هفته**
- کل پروژه: **12 هفته** (3 ماه)

---

## فاز 0: پایه‌گذاری (هفته 1)

### هدف
ایجاد زیرساخت پایه، CI/CD و محیط development

### Tasks

#### Infrastructure Setup
- [x] ایجاد repository در GitHub
- [x] تنظیم `.gitignore`, `.env.example`
- [x] ایجاد `docker-compose.yml` کامل
- [ ] راه‌اندازی GitHub Actions برای CI
- [ ] تنظیم pre-commit hooks

#### Development Environment
- [ ] راه‌اندازی Redis, PostgreSQL, RabbitMQ با Docker
- [ ] ایجاد schema پایگاه داده
- [ ] راه‌اندازی Prometheus + Grafana
- [ ] تنظیم logging infrastructure (Loki + Promtail)

#### Documentation
- [x] مستندات معماری با نمودارها
- [x] OpenAPI specification کامل
- [x] DEVELOPMENT.md
- [ ] TESTING.md
- [ ] CONTRIBUTING.md

**Deliverables**:
- ✅ محیط development قابل اجرا
- ✅ CI pipeline کار می‌کند
- ✅ Documentation پایه

**Estimated Time**: 5-7 روز

---

## فاز 1: MVP Core (هفته 2-3)

### هدف
پیاده‌سازی MCP Gateway و اتصال به Freqtrade

### Tasks

#### Week 2: MCP Gateway

**Backend (FastAPI)**
- [ ] Project structure setup
  ```
  services/mcp-gateway/
  ├── app/
  │   ├── main.py
  │   ├── routes/
  │   │   ├── candles.py
  │   │   ├── positions.py
  │   │   ├── orders.py
  │   │   └── health.py
  │   ├── models/
  │   ├── auth/
  │   │   ├── jwt.py
  │   │   └── hmac.py
  │   └── utils/
  ```

- [ ] Implement endpoints:
  - `GET /health`
  - `GET /candles`
  - `GET /positions/open`
  - `POST /orders/dry-run`
  - `POST /orders`

- [ ] JWT Authentication
- [ ] HMAC Signature validation
- [ ] Rate limiting middleware
- [ ] Error handling & logging

**Integration**
- [ ] Freqtrade REST API client
- [ ] WebSocket support (optional)
- [ ] Redis caching layer
- [ ] PostgreSQL logging

**Testing**
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests با Freqtrade mock
- [ ] Load testing (با locust/k6)

#### Week 3: Database & Monitoring

**Database Schema**
```sql
-- orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    request_id UUID UNIQUE,
    agent VARCHAR(50),
    pair VARCHAR(20),
    side VARCHAR(10),
    qty DECIMAL,
    type VARCHAR(10),
    status VARCHAR(20),
    created_at TIMESTAMP,
    meta JSONB
);

-- decisions table
CREATE TABLE decisions (
    id UUID PRIMARY KEY,
    request_id UUID,
    agent VARCHAR(50),
    pair VARCHAR(20),
    action VARCHAR(10),
    confidence DECIMAL,
    reasoning TEXT,
    llm_used BOOLEAN,
    created_at TIMESTAMP
);

-- llm_logs table
CREATE TABLE llm_logs (
    id UUID PRIMARY KEY,
    request_id UUID,
    input_hash VARCHAR(64),
    prompt TEXT,
    response TEXT,
    model VARCHAR(50),
    temperature DECIMAL,
    created_at TIMESTAMP
);
```

- [ ] Migration scripts (Alembic)
- [ ] Indexes optimization
- [ ] Connection pooling (PgBouncer)

**Monitoring**
- [ ] Prometheus metrics
  - Request rate, latency (p50, p95, p99)
  - Error rate
  - Active connections
- [ ] Grafana dashboards
- [ ] Alerting rules

**Deliverables**:
- ✅ MCP Gateway کاملاً عملیاتی
- ✅ اتصال موفق به Freqtrade
- ✅ Monitoring کار می‌کند

**Estimated Time**: 10-12 روز

---

## فاز 2: Multi-Agent System (هفته 4-5)

### هدف
پیاده‌سازی Orchestrator و Agents اولیه

### Tasks

#### Week 4: Orchestrator & Message Queue

**Orchestrator Service**
- [ ] FastAPI + Celery setup
- [ ] RabbitMQ integration
- [ ] Task routing logic
- [ ] State management (Redis)

**Message Flow**
```python
# Orchestrator receives candle update
@app.post("/webhook/candle")
async def handle_candle(candle_data: CandleUpdate):
    # 1. Validate
    # 2. Send to TOON encoding task
    # 3. Route to SignalAgent queue
    # 4. Await decision
    # 5. Route to RiskAgent
    # 6. Route to PositionManager
    pass
```

- [ ] Event-driven architecture
- [ ] Task queues setup:
  - `signal_queue`
  - `risk_queue`
  - `position_queue`
- [ ] Retry & error handling
- [ ] Circuit breaker pattern

#### Week 5: Agents Implementation

**SignalAgent**
- [ ] Celery worker setup
- [ ] Rule-based signals:
  - EMA crossover
  - RSI overbought/oversold
  - MACD divergence
  - Support/Resistance
- [ ] Decision fusion logic
- [ ] Confidence scoring
- [ ] Unit tests

**RiskAgent**
- [ ] Position sizing (ATR-based)
- [ ] Risk checks:
  - max_position_size
  - max_open_trades
  - daily_loss_limit
  - exposure_limit
- [ ] Kelly Criterion (optional)
- [ ] Stop-loss calculator
- [ ] Unit tests

**PositionManager**
- [ ] Order execution logic
- [ ] Dry-run validation
- [ ] HMAC signing
- [ ] Partial TP logic
- [ ] Trailing stop (basic)
- [ ] Unit tests

**Deliverables**:
- ✅ Orchestrator عملیاتی
- ✅ 3 agents کار می‌کنند
- ✅ End-to-end flow: candle → decision → order

**Estimated Time**: 10-14 روز

---

## فاز 3: LLM Integration & TOON (هفته 6-7)

### هدف
اضافه کردن LLM برای تصمیم‌گیری هوشمند و TOON encoding

### Tasks

#### Week 6: TOON Layer

**TOON Implementation**
```python
# services/orchestrator/app/toon/encoder.py

class TOONEncoder:
    def encode(self, df: pd.DataFrame, pair: str, tf: str) -> dict:
        """
        DataFrame → TOON object
        """
        # 1. Feature engineering
        df = self._add_features(df)

        # 2. Normalization
        df = self._normalize(df, method='zscore')

        # 3. Quantization (optional)
        df = self._quantize(df, buckets=16)

        # 4. Build TOON structure
        toon_obj = self._build_toon(df, pair, tf)

        # 5. Hash & cache
        toon_obj['input_hash'] = self._compute_hash(toon_obj)
        self._cache(toon_obj)

        return toon_obj
```

**Features**:
- [ ] Feature engineering module
  - RSI, ATR, MACD, EMA, BB
  - Volume indicators
  - Custom features
- [ ] Normalization strategies
  - Z-score
  - Min-max
  - Robust scaling
- [ ] Quantization (optional)
- [ ] Caching (Redis)
- [ ] Hash computation (SHA256)
- [ ] Unit tests

**Prompt Templates**
```python
SIGNAL_PROMPT = """
You are a cryptocurrency trading expert. Analyze the market data below and provide a trading decision.

Market: {pair}
Timeframe: {tf}
Current Price: {current_price}
Recent Regime: {regime}

Technical Indicators (last 10 candles):
{toon_data}

Recent Decisions:
{recent_decisions}

Provide your decision in JSON format:
{{
  "action": "buy|sell|hold",
  "confidence": 0.0-1.0,
  "reasoning": "...",
  "suggested_size_pct": 0.0-1.0,
  "suggested_sl": price,
  "suggested_tp": price
}}
"""
```

- [ ] Template engine
- [ ] Context builder (MemorySvc)
- [ ] Prompt versioning

#### Week 7: LLM Integration

**LLM Client**
- [ ] OpenAI client
- [ ] Anthropic client (optional)
- [ ] Local LLM support (optional)
- [ ] Response parsing & validation
- [ ] Retry logic + exponential backoff
- [ ] Rate limiting
- [ ] Cost tracking

**SignalAgent Enhancement**
```python
async def evaluate_signal(self, toon_data, context):
    # 1. Quick rule check
    rule_result = self._quick_rules(toon_data)
    if rule_result['confidence'] > 0.8:
        return rule_result

    # 2. Query LLM
    prompt = self._build_prompt(toon_data, context)
    llm_response = await self.llm.query(prompt)

    # 3. Parse & validate
    decision = self._parse_llm_response(llm_response)

    # 4. Fusion (if both available)
    if rule_result:
        decision = self._fuse(rule_result, decision)

    return decision
```

**Memory Service**
- [ ] Short-term memory (Redis)
- [ ] Long-term memory (PostgreSQL)
- [ ] Context retrieval
- [ ] Regime detection (trending/ranging/volatile)

**Deliverables**:
- ✅ TOON layer کار می‌کند
- ✅ LLM integration موفق
- ✅ Hybrid decision making

**Estimated Time**: 10-14 روز

---

## فاز 4: Replay Engine & Backtest (هفته 8-9)

### هدف
پیاده‌سازی بک‌تست قابل اعتماد با LLM Replay

### Tasks

#### Week 8: LLM Replay Engine

**Logging Infrastructure**
```python
# Every LLM call logs:
{
  "request_id": "uuid",
  "timestamp": 1690000000,
  "input_hash": "sha256...",
  "pair": "BTC/USDT",
  "tf": "15m",
  "prompt": "...",
  "llm_response": "{...}",
  "model": "gpt-4",
  "temperature": 0.0,
  "status": "ok"
}
```

- [ ] Structured logging (JSON)
- [ ] PostgreSQL storage + indexing
- [ ] S3/MinIO archival
- [ ] Replay lookup logic

**Replay Modes**
```python
class ReplayEngine:
    def replay(self, input_hash, mode='exact'):
        if mode == 'exact':
            return self._exact_match(input_hash)
        elif mode == 'nearest':
            return self._nearest_match(input_hash)
        elif mode == 'surrogate':
            return self._surrogate_predict(input_hash)
        else:  # fallback
            return self._default_policy()
```

- [ ] Exact match replay
- [ ] Nearest match (similarity search)
- [ ] Surrogate model placeholder
- [ ] Fallback to rules

#### Week 9: Backtest Framework

**Backtester**
- [ ] Historical data loader
- [ ] Event-driven simulation
- [ ] Portfolio tracking
- [ ] PnL calculation
- [ ] Trade log

**Metrics**
- [ ] CAGR, Sharpe, Sortino
- [ ] Max Drawdown
- [ ] Win Rate, Avg Trade PnL
- [ ] Turnover, Holding Time
- [ ] **Replay Coverage**: % exact matches

**API Endpoints**
- [ ] `POST /backtest` — start job
- [ ] `GET /backtest/{job_id}` — status & results
- [ ] Async execution (Celery)
- [ ] Results caching

**Deliverables**:
- ✅ Replay engine کار می‌کند
- ✅ Backtest framework عملیاتی
- ✅ نتایج قابل تکرار (reproducible)

**Estimated Time**: 10-12 روز

---

## فاز 5: Production Hardening (هفته 10-11)

### هدف
آماده‌سازی سیستم برای production

### Tasks

#### Week 10: Security & Resilience

**Security Enhancements**
- [ ] Secrets management (Vault/AWS Secrets Manager)
- [ ] mTLS برای inter-service communication
- [ ] Security headers (FastAPI middleware)
- [ ] Input sanitization
- [ ] SQL injection prevention
- [ ] OWASP Top 10 audit
- [ ] Penetration testing (basic)

**Resilience**
- [ ] Health checks برای تمام services
- [ ] Circuit breakers
- [ ] Graceful shutdown
- [ ] Auto-restart policies
- [ ] Database backup/restore
- [ ] Disaster recovery plan

**Observability**
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Error tracking (Sentry)
- [ ] Custom dashboards
- [ ] Alerting rules
  - High error rate
  - High latency (p95 > threshold)
  - Agent quarantine
  - Daily loss limit

#### Week 11: Performance & Scaling

**Performance Optimization**
- [ ] Database query optimization
- [ ] Redis caching strategy
- [ ] Connection pooling
- [ ] Async I/O optimization
- [ ] Load testing (target: 100 req/s)

**Horizontal Scaling**
- [ ] Kubernetes manifests
- [ ] HPA (Horizontal Pod Autoscaler)
- [ ] Service mesh (Istio optional)
- [ ] Load balancing

**Documentation**
- [ ] Deployment guide
- [ ] Runbooks (incident response)
- [ ] API documentation (Swagger UI)
- [ ] Architecture Decision Records (ADRs)

**Deliverables**:
- ✅ سیستم امن و resilient
- ✅ Performance targets برآورده شده
- ✅ آماده برای production deployment

**Estimated Time**: 10-14 روز

---

## فاز 6: Advanced Features (هفته 12+)

### هدف
بهبودهای پیشرفته و optimization

### Tasks (اولویت پایین‌تر)

#### MetaAgent
- [ ] عملکرد monitoring
- [ ] Hyperparameter tuning (Optuna)
- [ ] Trigger retrain
- [ ] Quarantine logic

#### Surrogate Model
- [ ] Data collection از logs
- [ ] Train XGBoost/LightGBM
- [ ] Fine-tune transformer (optional)
- [ ] A/B testing vs LLM

#### UI/Dashboard
- [ ] React/Vue frontend
- [ ] Real-time position tracking
- [ ] Decision explanation view
- [ ] Performance analytics

#### Advanced Risk
- [ ] Portfolio optimization
- [ ] Correlation analysis
- [ ] Dynamic position sizing
- [ ] VaR (Value at Risk)

**Deliverables**:
- ✅ MetaAgent عملیاتی
- ✅ Surrogate model کار می‌کند
- ✅ Dashboard حرفه‌ای

**Estimated Time**: 2-4 هفته (ongoing)

---

## Milestones

### M0: Foundation Complete ✅
**Deadline**: End of Week 1  
**Criteria**:
- docker-compose up works
- Monitoring stack running
- Documentation complete

### M1: MVP Core
**Deadline**: End of Week 3  
**Criteria**:
- MCP Gateway passes all tests
- Successfully connects to Freqtrade
- Can retrieve candles & execute orders

### M2: Multi-Agent System
**Deadline**: End of Week 5  
**Criteria**:
- 3 agents operational
- End-to-end flow works
- >80% test coverage

### M3: LLM Integration
**Deadline**: End of Week 7  
**Criteria**:
- TOON encoding working
- LLM making decisions
- Hybrid fusion successful

### M4: Backtest Ready
**Deadline**: End of Week 9  
**Criteria**:
- Replay engine working
- Backtest produces valid results
- Replay coverage > 70%

### M5: Production Ready 🚀
**Deadline**: End of Week 11  
**Criteria**:
- Security audit passed
- Performance targets met
- Deployed to staging successfully

---

## KPIs هر فاز

### فاز 1 (MVP Core)
- **Code Coverage**: > 80%
- **API Response Time (p95)**: < 200ms
- **Uptime**: > 99%

### فاز 2 (Multi-Agent)
- **End-to-end Latency**: < 5s (candle → order)
- **Agent Success Rate**: > 95%
- **Test Coverage**: > 85%

### فاز 3 (LLM)
- **LLM Query Time (p95)**: < 10s
- **Decision Confidence**: avg > 0.7
- **Cost per Decision**: < $0.05

### فاز 4 (Backtest)
- **Replay Coverage**: > 70%
- **Backtest Speed**: 1 year in < 10 min
- **Reproducibility**: 100% (same inputs = same output)

### فاز 5 (Production)
- **System Uptime**: > 99.5%
- **p95 Latency**: < 200ms (all APIs)
- **Security Vulnerabilities**: 0 high/critical

---

## GitHub Project Board

استفاده از **GitHub Projects** برای tracking:

**Columns**:
1. **Backlog**: تمام tasks آینده
2. **Todo**: tasks برای sprint جاری
3. **In Progress**: در حال کار
4. **In Review**: منتظر code review
5. **Testing**: در حال تست
6. **Done**: تکمیل شده

**Labels**:
- `phase-0`, `phase-1`, ..., `phase-6`
- `priority-high`, `priority-medium`, `priority-low`
- `type-feature`, `type-bug`, `type-docs`, `type-test`
- `component-mcp`, `component-orchestrator`, `component-agent`, etc.

---

## سوالات متداول

**Q: چرا 12 هفته؟**  
A: برای MVP واقعی 6 هفته کافی است. 6 هفته اضافی برای production hardening و advanced features است.

**Q: اگر تیم بزرگتری داشته باشیم؟**  
A: با 3-4 developer می‌توان زمان را به 6-8 هفته کاهش داد (parallelization بیشتر).

**Q: اولویت‌ها چطور؟**  
A: فاز 0-4 ضروری هستند. فاز 5 برای production لازم است. فاز 6 nice-to-have است.

**Q: چگونه progress را track کنیم؟**  
A: از GitHub Projects + این ROADMAP استفاده کنید. هر sprint یک review meeting داشته باشید.

---

**آخرین به‌روزرسانی**: 2025-11-18  
**نسخه**: 1.0  
**نگهدارنده**: Multi-Agent Team
