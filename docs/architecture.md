# معماری کلی — Multi-Agent Hybrid Trading Robot

هدف این سند خلاصه و تشریح معماری پیشنهادی برای ربات معاملاتی هیبریدی (Freqtrade + TOON + LLM) است. طراحی به‌گونه‌ای است که مقیاس‌پذیر، امن و قابل تست باشد.

## اجزا (Overview)
- Orchestrator: هماهنگ‌کننده و صف پیام‌ها، مدیریت نرخ تماس با LLM و زمان‌بندی اجرای agentها.
- MCP Gateway: درگاه امن برای خواندن/نوشتن وضعیت Freqtrade (REST/gRPC).
- SignalAgent: تولید سیگنال‌ها (hybrid: rules + LLM).
- RiskAgent: محاسبه اندازه پوزیشن، کنترل اکسپوژر و failsafeها.
- PositionManager: اجرای سفارش‌ها، مدیریت trailing/partial TP.
- MemorySvc: حافظه کوتاه‌مدت (Redis) و تاریخچه بلند‌مدت (Postgres / S3 archive).
- LLM Replay Engine: ضبط پاسخ‌ها برای replay در بک‌تست (deterministic replay).
- Monitoring & UI: داشبورد، آلارم‌ها و ابزارهای explainability.

## جریان داده (High-level Data Flow)
1. Freqtrade تولید یا آپدیت کندل ⇒ MCP (webhook یا poll).
2. Orchestrator کندل را دریافت و به TOON Layer می‌سپارد.
3. TOON خروجی را encode می‌کند و آن را به SignalAgent ارسال می‌کند.
4. SignalAgent تصمیم اولیه را با heuristics می‌گیرد؛ در صورت نیاز، پرامپت TOON به LLM ارسال می‌شود.
5. خروجی LLM (JSON) parse و توسط RiskAgent ارزیابی می‌شود.
6. PositionManager پس از dry-run در MCP، سفارش را اجرا می‌کند.
7. MemorySvc و لاگ‌ها به‌روزرسانی شده و UI نمایش داده می‌شود.

## امنیت و محدودیت‌ها
- ارتباط میان سرویس‌ها با JWT یا mTLS.
- whitelist کردن فرمان‌های اجرایی در MCP.
- rate-limiting و backoff برای تماس با LLM.

## نکات عملی
- طراحی هر Agent به صورت سرویس مستقل (کانتینر) برای تسهیل مقیاس و ایزولیشن.
- همه تصمیمات باید لاگ و با شناسه‌ی یکتا (request_id) ثبت شوند تا replay و audit ممکن باشد.
