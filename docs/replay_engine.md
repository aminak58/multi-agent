# LLM Replay Engine — طراحی برای بک‌تست بازتولیدپذیر

این سند فرمت لاگ‌ها، الگوریتم replay و استراتژی‌های fallback و surrogate model را تشریح می‌کند تا بک‌تست دقیق و deterministic ممکن شود.

## اهداف
- ضبط تمام پرامپت‌ها و پاسخ‌های LLM در محیط live/paper با metadata کافی.
- برای بک‌تست تاریخی، امکان بازپخش (replay) دقیق پاسخ‌های LLM بر اساس input_hash و timestamp فراهم شود.

## فرمت لاگ (record schema)
- هر رکورد (row) JSON به‌صورت newline-delimited ذخیره شود و فیلدهای زیر را داشته باشد:
```json
{
  "request_id":"uuid",
  "timestamp":1690000000,
  "input_hash":"sha256...",
  "pair":"BTC/USDT",
  "tf":"15m",
  "prompt": "...",
  "llm_response": "{...}",
  "model":"gpt-x",
  "temperature":0.0,
  "response_hash":"sha256...",
  "status":"ok"
}
```

## ذخیره‌سازی و ایندکس
- ذخیرهٔ لاگ‌ها در Postgres (برای جستجو) و S3-compatible bucket برای آرشیو طولانی‌مدت. همچنین یک copy در Redis index برای lookup سریع بر اساس `input_hash`.
- ایندکس پیشنهادی: (`input_hash`, `timestamp`, `pair`, `tf`).

## الگوریتم replay (deterministic)
1. Backtester هر بار که به نقطه‌ای می‌رسد که در اجرا live/paper یک پرامپت تولید شده است، `input_hash` مشابه را محاسبه می‌کند.
2. اگر exact match در لاگ موجود باشد، همان `llm_response` بازگردانده می‌شود. (deterministic)
3. اگر exact match پیدا نشود، fallback options:
   - a) nearest-match: جستجو بر اساس `input_hash` proximity یا نزدیک‌ترین `timestamp` برای همان `pair`+`tf`.
   - b) surrogate model: یک مدل سبک (مثلاً fine-tuned transformer کوچک یا classifier) که برای تولید پاسخ شبیه به LLM آموزش داده شده است.
   - c) default policy: `hold` یا قوانین پیش‌فرض که deterministic هستند.

## surrogate model plan
- داده‌های لاگ استفاده شده برای آموزش: `{prompt, llm_response, parsed_decision}` — train supervised model برای map prompt -> parsed_decision.
- مدل پیشنهادی برای MVP: XGBoost classifier/regressor برای decision class و مقادیر numeric (size_pct)، یا یک transformer کوچک (distil-like) در صورت نیاز به حفظ بافت reasoning.

## اعتبارسنجی replay
- برای هر بازپخش، گزارش تطبیقی تولید کنید که تفاوت بین پاسخ replayed و live را نشان دهد (در صورت استفاده از surrogate یا nearest-match).
- متریکها: replay_coverage (درصد prompts که exact-match دارند)، surrogate_error_rate.

## لاگ سطح بالاتر برای audit
- علاوه بر prompt/response، لاگ‌های نهایی مرتبط با اجرا (dry-run result, executed_order, pnl_delta) نیز باید مرتبط با همان `request_id` ذخیره شوند.

## نمونهٔ پیاده‌سازی (pseudo)
```python
def replay_response(input_hash, pair, tf, timestamp):
    rec = db.get_by_input_hash(input_hash)
    if rec:
        return rec['llm_response']
    # nearest
    rec2 = db.find_nearest(input_hash, pair, tf)
    if rec2:
        return rec2['llm_response']
    # surrogate
    return surrogate.predict(prompt_from_hash(input_hash))
```

## نکات عملی
- لاگ‌ها را با مرتبهٔ زمانی، request_id و input_hash هماهنگ کنید تا replay کاملاً traceable باشد.
- برای تست reproducibility، یک test-suite داشته باشید که برای یک هفتهٔ live logs، backtest با replay دقیقا نتایج را بازتولید کند.
