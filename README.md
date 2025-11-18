# multi-agent

ربات معاملاتی چندعاملی (Hybrid) برای استفاده همراه با Freqtrade — ترکیب TOON برای نمایش/فشرده‌سازی داده و LLM برای تصمیم‌گیری تطبیقی.

ویژگی‌های کلیدی
- معماری Multi-Agent: SignalAgent، RiskAgent، PositionManager و سرویس حافظه (MemorySvc).
- MCP Gateway برای تعامل امن با Freqtrade (REST/gRPC). 
- قابلیت "یادگیری در زمان اجرا" و بازآموزی دوره‌ای، و LLM Replay Engine برای بک‌تست بازتولیدپذیر.
- تاکید بر explainability، logging کامل و قواعد ایمنی قبل از اجرای سفارش.

فایل‌های مهم
- `docs/architecture.md` — نمای کلی معماری
- `docs/api.md` — مشخصات MCP و قراردادهای پیام
- `docs/agents.md` — شرح agentها و نمونه پیام‌ها
- `docs/deployment.md` — راه‌اندازی محلی (MVP) با docker-compose

شروع سریع (محلی)
1. پیش‌نیازها: نصب `Docker`, `docker-compose`, `git`, `gh` و `Python 3.10+` (در صورت نیاز).
2. کلون/موقعیت پروژه:
	```powershell
	cd C:\FreqtradeProjects\multi-agent
	```
3. اجرای MVP با Docker Compose:
	```powershell
	docker-compose up --build
	```

چگونه کمک کنید / مشارکت
- ایده‌ها، باگ‌ها و درخواست‌ها را در ریپازیتوری GitHub ثبت کنید.
- برای توسعه محلی، مستندات داخل پوشه `docs/` را دنبال کنید.

مجوز
- برای حالتی که تمایل دارید، یک `LICENSE` اضافه کنید؛ تا قبل از آن این مخزن بدون مجوز خاص در دست توسعه است.

ارتباط
- برای نکات یا راهنمایی سریع، متن موردنظر README یا سوال خود را در issue یا اینجا ارسال کنید.
