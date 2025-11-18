# API و پیام‌ها — MCP Gateway (نمونه)

این فایل مشخصات پایهٔ REST API پیشنهادی برای MCP Gateway را نشان می‌دهد. هدف ارائهٔ یک اینترفیس امن و قابل آزمون برای تعامل agentها با Freqtrade است.

## اصول طراحی
- REST یا gRPC قابلِ پشتیبانی؛ برای MVP از FastAPI (REST) استفاده کنید.
- احراز هویت: JWT یا mTLS. هر درخواست با `Authorization: Bearer <token>` ارسال شود.
- هر درخواست باید یک `request_id` (UUID) داشته باشد تا traceability برقرار شود.

## Endpoints پیشنهادی

- `GET /candles?pair={pair}&tf={tf}&n={n}`
  - توضیح: برگرداندن n کندل آخر همراه با featureهای پایه.
  - پاسخ نمونه:
    ```json
    [{"t":169..., "o":..., "h":..., "l":..., "c":..., "v":..., "rsi":45, "atr":0.5}, ...]
    ```

- `GET /positions/open`
  - توضیح: لیست پوزیشن‌های باز.
  - پاسخ نمونه:
    ```json
    [{"id":"uuid","pair":"BTC/USDT","side":"long","size":0.01,"entry_price":56000}]
    ```

- `POST /orders`
  - توضیح: ایجاد سفارش جدید یا درخواست اجرای order توسط PositionManager.
  - بدنهٔ نمونه:
    ```json
    {"request_id":"uuid","agent":"SignalAgent/v1","pair":"BTC/USDT","side":"buy","qty":0.001,"type":"market","meta":{}}
    ```
  - پاسخ نمونه:
    ```json
    {"ok":true, "order_id":"abc123","status":"submitted"}
    ```

- `POST /orders/dry-run`
  - توضیح: شبیه‌سازی پیش از اجرای نهایی برای بررسی risk checks.
  - پاسخ نمونه:
    ```json
    {"ok":true, "warnings":[], "margin_required":0.12}
    ```

- `POST /backtest`
  - توضیح: راه‌اندازی یک job بک‌تست با پارامترها و بازگرداندن job id.

## قرارداد پیام LLM
- ورودی LLM: TOON-encoded data + context (last decisions, regime) + instruction template.
- خروجی LLM باید JSON معتبر با schema زیر باشد:
  ```json
  {
    "action":"buy|sell|hold",
    "confidence":0.0,
    "reasoning":"string",
    "suggested_size_pct":0.0,
    "suggested_sl":0.0,
    "suggested_tp":0.0,
    "features":["string"]
  }
  ```

## امنیت و اعتبارسنجی
- قبل از اجرای هر `POST /orders` درخواست dry-run انجام شود.
- whitelist agentها: فقط agents شناخته‌شده اجازه‌ی فرستادن درخواست اجرایی را دارند.
