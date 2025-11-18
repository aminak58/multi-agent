# مشخصات Agentها و پیام‌ها

این سند نقش هر agent، قراردادهای پیام، و نمونه‌های اسکلتی از کد را شرح می‌دهد.

## فهرست Agentها
- SignalAgent
- RiskAgent
- PositionManager
- MetaAgent (اختیاری)

### SignalAgent
- ورودی: TOON-encoded candles و context
- خروجی: JSON تصمیم (action, confidence, reasoning, suggested_size_pct, suggested_sl, suggested_tp)
- منطق: ابتدا قوانین ساده (EMA, RSI, support/resistance) اجرا شود؛ در صورت ambiguous، LLM فراخوانی شود.

### RiskAgent
- وظیفه: position sizing، بررسی exposure و محدودیت‌های ایمنی
- API محاسبه اندازه پوزیشن:
  - `position_size = RiskAgent.compute_size(portfolio_value, instrument_vol, params)`

### PositionManager
- وظیفه: اجرای سفارش‌ها از طریق MCP؛ مدیریت partial TP و trailing
- قبل از ارسال به MCP، dry-run را صدا می‌زند و در صورت OK، سفارش را ارسال می‌کند.

### MetaAgent
- وظیفه: مانیتورینگ عملکرد agentها، تنظیم alpha در fusion، trigger retrain و quarantine کردن agentها در صورت رفتار نامتعارف.

## نمونهٔ اسکلت (ساختار فایل‌ها)
- `agents/`
  - `base.py` — کلاینت MCP مشترک
  - `signal_agent.py` — اسکلت SignalAgent
  - `risk_agent.py` — پیاده‌سازی sizing
  - `position_manager.py` — اجرای سفارشات

### نمونهٔ request/response (SignalAgent → Orchestrator)
```json
{
  "request_id":"uuid",
  "agent":"SignalAgent/v1",
  "pair":"BTC/USDT",
  "tf":"15m",
  "decision":{
    "action":"buy",
    "confidence":0.78,
    "reasoning":"macd_crossover + rsi_rising",
    "suggested_size_pct":0.02
  }
}
```
