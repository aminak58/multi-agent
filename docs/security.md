# Security — احراز هویت، امضا و سیاست‌های rate-limit

این سند سیاست‌های امنیتی برای MCP و ارتباط agentها با LLM و Freqtrade را توضیح می‌دهد. موارد زیر دقیقاً مطابق با نیازهای سند اولیه طراحی شده‌اند.

## اصول کلی
- همهٔ سرویس‌ها باید authenticated و authorized باشند (least privilege).
- ارتباطات سرویس‌ها باید رمزگذاری‌شده باشند (TLS)؛ در محیط production مِدل mTLS ترجیح داده می‌شود.

## احراز هویت و authorization
- JWT برای سرویس‌ها: هر سرویس یک client_id دارد و از طریق یک Identity Provider (simple JWT issuer برای MVP) توکن می‌گیرد.
- توکن‌ها شامل claims: `iss`, `sub`, `aud`, `exp`, `roles` (مثلاً `signal_agent`, `risk_agent`, `position_manager`).
- هر endpoint در MCP role-based access control (RBAC) دارد: مثلاً `POST /orders` فقط برای role `position_manager` یا agents مشخص شده مجاز است.

## HMAC signing برای دستورات حساس
- برای دستورهای حساس (مثلاً اجرای سفارش)، علاوه بر JWT، پیام باید HMAC-SHA256 با یک secret خاص سرویس امضا شود تا تضمین authenticity payload داشته باشیم.
- نمونهٔ امضا (pseudo):
```python
import hmac, hashlib
def sign_payload(secret, payload_bytes):
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
```
- MCP قبل از اجرای دستور HMAC را بررسی می‌کند و mismatch باعث reject و audit log می‌شود.

## window validation و replay-attack prevention
- هر درخواست اجرایی باید دارای `timestamp` باشد و MCP تنها درخواست‌هایی با اختلاف زمانی کمتر از `max_skew` (مثلاً 30s) بپذیرد.
- `nonce` یا `request_id` باید یکتا باشد؛ ذخیره‌سازی برای window زمانی برای جلوگیری از replay attacks.

## Rate limiting و backoff
- هر agent یک policy محلی برای تماس با LLM داشته باشد: leaky-bucket یا token-bucket.
- نمونه policy برای MVP:
  - max_calls_per_minute = 60
  - concurrent_calls = 2
  - on_429: exponential backoff up to 60s

## Auditing و لاگ‌ امن
- لاگ‌های پرامپت و پاسخ LLM حساس محسوب می‌شوند؛ دسترسی به آن‌ها محدود شود.
- لاگ‌ها باید با `request_id`, `user/agent`, `timestamp`, `input_hash` همراه باشند تا audit امکان‌پذیر باشد.

## مدیریت اسرار
- از Vault یا AWS Secrets Manager برای نگهداری secretهای HMAC، JWT signing keys و API keys استفاده کنید.
- دسترسی به secrets بر مبنای نقش و با MFA (در صورت دسترسی انسان) باشد.

## incident response
- اگر mismatch HMAC یا تعداد خطاهای مشکوک مشاهده شود:
  1. quarantize agent (suspend calls)
  2. alert ops on-call
  3. rotate secret keys in Vault و reissue tokens
