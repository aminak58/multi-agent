# TOON Layer — طراحی و پیاده‌سازی

این سند شرح فنیِ `TOON` (Tokenized/Typed Observational Notation) برای encode کردن داده‌های زمانی (candles + features) است تا آن‌ها را به‌صورت کارآمد و قابل‌فهم برای LLM ارسال کنیم. همهٔ توضیحات و نمونه‌ها مطابق با نیازهای سند اولیه شما نوشته شده‌اند.

## هدف
- کاهش پهنای باند پرامپتِ ارسالی به LLM با حفظ ویژگی‌های کلیدی سری زمانی.
- تولید قالبی deterministic و قابل-hash برای replay deterministic در LLM Replay Engine.

## ورودی و خروجی
- ورودی: pandas.DataFrame از کندل‌ها با ستون‌های `t, o, h, l, c, v` و ستون‌های مشتق‌شده (features) مثل `rsi`, `atr`, `macd`, `ema_fast`, `ema_slow`.
- خروجی: یک آرایهٔ JSON کوچک از آبجکت‌های فشرده‌شده یا یک رشته TOON که LLM قادر به پردازش آن است.

## مراحل تبدیل (پیشنهادی)
1. Feature engineering پایه: محاسبه `ATR(14)`, `RSI(14)`, `EMA(8)`, `EMA(21)`, `MACD`، `volume_zscore` و دیگر featureهایی که در docs ذکر شده.
2. Normalization:
   - پیش‌فرض: z-score با استفاده از rolling window (مثلاً 200 کندل). برای داده‌های outlier-prone می‌توان از robust scaling (median & IQR) استفاده کرد.
   - پارامترها configurable باشند: `method: zscore|minmax|robust`, `window: int`.
3. Compression / tokenization:
   - حذف فیلدهای غیرضروری (مثلاً ارسال تنها `c` به‌جای `o,h,l,c` اگر bandwidth محدود باشد) بسته به template پرامپت.
   - برای هر feature عددی، quantize به k-buckets (مثلاً 16 یا 32) در صورت نیاز به کاهش طول ورودی.
4. Build TOON structure:
   - نمونهٔ TOON (JSON):
     ```json
     {
       "pair":"BTC/USDT",
       "tf":"15m",
       "last_ts":1690000000,
       "data":[{"t":169...,"c_q":12,"rsi_q":6,"atr_q":3},...],
       "features_list":["c_q","rsi_q","atr_q"]
     }
     ```

## Hashing و caching
- برای هر TOON یک `input_hash = sha256(pair + tf + last_ts + feature_list + data_digest)` محاسبه کنید.
- کش Redis با کلید `toon:{input_hash}` و TTL قابل تنظیم (پیشنهاد: 30s برای real-time، 5m برای backtest/archive) استفاده شود.

## APIهای پیشنهادی
- `dataframe_to_toon(df, pair, tf, normalize_method='zscore', quantize_buckets=16) -> dict`
- `toon_to_prompt(toon_obj, template) -> str` — تولید پرامپت نهایی برای LLM

## مثال کد (اسکلت)
```python
def dataframe_to_toon(df, pair, tf, normalize_method='zscore', window=200, buckets=16):
    # محاسبه featureها
    df['atr'] = atr(df['h'], df['l'], df['c'], window=14)
    df['rsi'] = rsi(df['c'], window=14)
    # نرمال‌سازی
    df['rsi_n'] = (df['rsi'] - df['rsi'].rolling(window).mean()) / df['rsi'].rolling(window).std()
    # کوانتیزه
    df['rsi_q'] = pd.qcut(df['rsi_n'].rank(method='first'), buckets, labels=False, duplicates='drop')
    toon = { 'pair': pair, 'tf': tf, 'last_ts': int(df['t'].iat[-1]), 'data': [] }
    for _, row in df.tail(50).iterrows():
        toon['data'].append({'t': int(row['t']), 'c_q': int(row['rsi_q'])})
    # hash و بازگشت
    toon['input_hash'] = compute_hash(toon)
    return toon
```

## تست واحد پیشنهادی
- تَست‌ها باید تضمین کنند: deterministic hash برای ورودی یکسان، تطابق quantization، و TTL cache کار می‌کند.

## نکات عملی
- طول نهایی توکن محدود است؛ بنابراین template پرامپت باید flexible باشد و تنها featureهای کلیدی را وارد کند.
- TOON باید human-readable نیز باشد (برای explainability) اما همچنان compact.
