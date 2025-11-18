# راهنمای مشارکت — Multi-Agent Trading Bot

از اینکه به مشارکت در این پروژه علاقه‌مند هستید، سپاسگزاریم! 🎉

این سند راهنمای کامل نحوه مشارکت در پروژه را ارائه می‌دهد.

## فهرست

1. [Code of Conduct](#code-of-conduct)
2. [چطور می‌توانم کمک کنم؟](#چطور-میتوانم-کمک-کنم)
3. [شروع سریع](#شروع-سریع)
4. [Git Workflow](#git-workflow)
5. [استانداردهای کد](#استانداردهای-کد)
6. [Commit Messages](#commit-messages)
7. [Pull Request Process](#pull-request-process)
8. [Review Process](#review-process)
9. [سوالات متداول](#سوالات-متداول)

---

## Code of Conduct

ما متعهد به ایجاد یک محیط باز، خوشایند و بدون تبعیض هستیم. از همه مشارکت‌کنندگان انتظار داریم:

- ✅ با احترام با دیگران رفتار کنند
- ✅ از زبان مناسب استفاده کنند
- ✅ نظرات دیگران را بپذیرند
- ✅ بر بهبود پروژه تمرکز کنند

❌ رفتارهای غیرقابل قبول:
- زبان توهین‌آمیز یا تبعیض‌آمیز
- حملات شخصی یا سیاسی
- Trolling یا تحریک عمدی
- انتشار اطلاعات خصوصی دیگران

**گزارش رفتار نامناسب**: اگر رفتار نامناسبی مشاهده کردید، به [conduct@your-domain.com](mailto:conduct@your-domain.com) گزارش دهید.

---

## چطور می‌توانم کمک کنم؟

### 1. گزارش باگ 🐛

اگر باگی پیدا کردید:

1. **بررسی کنید** که قبلاً گزارش نشده باشد: [Issues](https://github.com/your-org/multi-agent/issues)
2. **Issue جدید** با template "Bug Report" ایجاد کنید
3. **اطلاعات کامل** ارائه دهید:
   - مراحل بازتولید (Reproduction Steps)
   - نتیجه مورد انتظار vs واقعی
   - محیط (OS, Python version, Docker version)
   - Logs و error messages
   - Screenshots (در صورت لزوم)

**مثال Bug Report خوب**:

```markdown
### توضیح
MCP Gateway با خطای 500 fail می‌شود وقتی بیش از 100 کندل درخواست شود.

### مراحل بازتولید
1. `docker-compose up`
2. `curl "http://localhost:8000/api/v1/candles?pair=BTC/USDT&tf=15m&n=150"`
3. خطای 500 دریافت می‌شود

### نتیجه مورد انتظار
باید 150 کندل برگردانده شود یا خطای validation مناسب.

### محیط
- OS: Ubuntu 22.04
- Docker: 24.0.5
- Python: 3.10

### Logs
```
ERROR - IndexError: list index out of range at line 42
```

### پیشنهاد راه‌حل
اضافه کردن validation برای max candles در route handler.
```

### 2. پیشنهاد ویژگی جدید 💡

برای پیشنهاد feature جدید:

1. **بحث اولیه**: ابتدا در [Discussions](https://github.com/your-org/multi-agent/discussions) مطرح کنید
2. **Issue جدید** با template "Feature Request" ایجاد کنید
3. **توضیح کامل**:
   - مشکلی که حل می‌کند
   - پیشنهاد implementation
   - Alternatives در نظر گرفته شده
   - تاثیر بر performance/security

### 3. بهبود مستندات 📝

مستندات همیشه نیاز به بهبود دارند:

- تصحیح اشتباهات املایی/گرامری
- اضافه کردن مثال‌های بیشتر
- بهبود توضیحات
- ترجمه به زبان‌های دیگر
- اضافه کردن diagrams/screenshots

### 4. نوشتن تست 🧪

تست‌ها همیشه خوش‌آمد هستند:

- Unit tests برای توابع جدید
- Integration tests برای جریان‌های end-to-end
- Performance tests
- بهبود coverage

### 5. پیاده‌سازی Features 💻

اگر می‌خواهید کد بنویسید:

1. یک issue موجود پیدا کنید یا جدید ایجاد کنید
2. در issue comment کنید که روی آن کار می‌کنید
3. به workflow زیر عمل کنید

---

## شروع سریع

### 1. Fork & Clone

```bash
# Fork repository در GitHub UI

# Clone fork خودتان
git clone https://github.com/YOUR_USERNAME/multi-agent.git
cd multi-agent

# Add upstream remote
git remote add upstream https://github.com/your-org/multi-agent.git
```

### 2. محیط توسعه

```bash
# ایجاد venv
python -m venv venv
source venv/bin/activate  # یا venv\Scripts\activate در Windows

# نصب dependencies
pip install -r requirements-dev.txt

# نصب pre-commit hooks
pre-commit install
```

### 3. بررسی کارکرد

```bash
# راه‌اندازی با Docker
docker-compose up -d

# اجرای تست‌ها
pytest -v

# Linting
flake8 services/
```

---

## Git Workflow

ما از **Feature Branch Workflow** استفاده می‌کنیم:

### 1. ایجاد Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-feature

# یا برای fix:
git checkout -b fix/bug-description
```

**نامگذاری Branches**:
- `feature/description` - برای features جدید
- `fix/description` - برای bug fixes
- `docs/description` - برای تغییرات documentation
- `refactor/description` - برای refactoring
- `test/description` - برای تست‌ها

### 2. Develop

```bash
# تغییرات خود را اعمال کنید
# ...

# Commit frequently (atomic commits)
git add .
git commit -m "feat: add feature X"

# Push به fork
git push origin feature/my-feature
```

### 3. Sync با Upstream

```bash
# هر روز یا قبل از PR
git fetch upstream
git rebase upstream/main

# حل conflict (در صورت وجود)
git rebase --continue
```

### 4. Create Pull Request

1. برو به fork خودت در GitHub
2. "Compare & pull request" کلیک کن
3. Template PR را پر کن
4. منتظر review بمان

---

## استانداردهای کد

### Python Style Guide

ما از **PEP 8** با کمی تغییرات استفاده می‌کنیم:

```python
# ✅ خوب
def calculate_position_size(
    portfolio_value: float,
    risk_pct: float,
    atr: float,
) -> float:
    """
    محاسبه اندازه پوزیشن بر اساس ATR.

    Args:
        portfolio_value: ارزش کل پورتفولیو
        risk_pct: درصد ریسک (0.0-1.0)
        atr: ATR فعلی

    Returns:
        اندازه پوزیشن

    Raises:
        ValueError: اگر ورودی‌ها نامعتبر باشند
    """
    if risk_pct < 0 or risk_pct > 1:
        raise ValueError("risk_pct must be between 0 and 1")

    risk_amount = portfolio_value * risk_pct
    position_size = risk_amount / (atr * 2)

    return position_size


# ❌ بد
def calc_pos(pv,r,a):  # نامگذاری بد، بدون type hints، بدون docstring
    return pv*r/(a*2)
```

**قوانین**:
- ✅ Max line length: **100 characters**
- ✅ Type hints برای **تمام** توابع
- ✅ Docstrings (Google style) برای کلاس‌ها و توابع public
- ✅ نامگذاری: `snake_case` برای functions/variables، `PascalCase` برای classes
- ✅ Import order: standard library → third-party → local
- ✅ از `isort` برای sorting imports استفاده کنید

### Testing Standards

```python
# ✅ خوب
import pytest
from unittest.mock import Mock, patch


class TestSignalAgent:
    """Test suite for SignalAgent."""

    @pytest.fixture
    def agent(self):
        """Create a SignalAgent instance for testing."""
        return SignalAgent(mcp_url="http://test", llm_config={})

    def test_evaluate_signal_with_clear_buy(self, agent):
        """
        Test که agent برای سیگنال واضح buy تصمیم درست می‌گیرد.

        Given: MACD crossover bullish + RSI < 30
        When: evaluate_signal called
        Then: action = 'buy', confidence > 0.7
        """
        # Arrange
        candles = self._create_bullish_candles()

        # Act
        decision = agent.evaluate_signal(candles)

        # Assert
        assert decision['action'] == 'buy'
        assert decision['confidence'] > 0.7
        assert 'macd' in decision['reasoning'].lower()
```

**قوانین**:
- ✅ Coverage > **80%**
- ✅ نامگذاری: `test_<method>_<scenario>_<expected>`
- ✅ AAA pattern: Arrange, Act, Assert
- ✅ از fixtures برای setup استفاده کنید
- ✅ Mock external dependencies

### Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# ✅ خوب
logger.info(
    "Signal generated",
    extra={
        "pair": "BTC/USDT",
        "action": "buy",
        "confidence": 0.82,
        "request_id": request_id,
    }
)

# ❌ بد
print(f"Signal: buy BTC")  # از print استفاده نکنید!
```

**Levels**:
- `DEBUG`: اطلاعات detailed برای debugging
- `INFO`: رویدادهای عادی
- `WARNING`: مشکلات احتمالی
- `ERROR`: خطاهای قابل handle
- `CRITICAL`: خطاهای جدی که سیستم را متوقف می‌کنند

---

## Commit Messages

ما از **Conventional Commits** استفاده می‌کنیم:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | کاربرد |
|------|---------|
| `feat` | Feature جدید |
| `fix` | رفع bug |
| `docs` | تغییرات documentation |
| `style` | Formatting (بدون تغییر منطق) |
| `refactor` | Refactoring کد |
| `test` | اضافه/اصلاح تست |
| `chore` | Build/config changes |
| `perf` | بهبود performance |
| `ci` | تغییرات CI/CD |

### Scopes (اختیاری)

- `mcp-gateway`
- `orchestrator`
- `signal-agent`
- `risk-agent`
- `position-manager`
- `toon`
- `replay-engine`
- `docs`

### مثال‌ها

```bash
# Simple
feat(signal-agent): add MACD crossover detection

# با body
fix(mcp-gateway): handle connection timeout errors

When Redis connection times out, the gateway crashes.
This commit adds retry logic with exponential backoff.

Fixes #123

# Breaking change
feat(api)!: change order response structure

BREAKING CHANGE: order_id field renamed to id in response
```

**قوانین**:
- ✅ Subject: حداکثر 50 کاراکتر، imperative mood ("add" نه "added")
- ✅ Body: wrap به 72 کاراکتر، توضیح "چرا" نه "چی"
- ✅ Footer: لینک به issues (`Fixes #123`, `Closes #456`)

---

## Pull Request Process

### 1. قبل از PR

**Checklist**:
- [ ] Code passes all tests (`pytest`)
- [ ] Code passes linting (`flake8`, `pylint`)
- [ ] Code formatted (`black`, `isort`)
- [ ] Coverage > 80% (برای خطوط جدید)
- [ ] Documentation updated
- [ ] Changelog updated (در صورت لزوم)
- [ ] Commits follow convention

### 2. PR Template

```markdown
## خلاصه
توضیح کوتاه تغییرات (1-2 جمله)

## نوع تغییر
- [ ] Bug fix
- [ ] Feature جدید
- [ ] Breaking change
- [ ] Documentation update

## شرح
توضیح کامل:
- مشکل چیست؟
- چطور حل شده؟
- چرا این رویکرد؟

## تست
چطور تست کردید؟
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] Performance testing

## Screenshots (در صورت لزوم)

## Checklist
- [ ] Code follows style guide
- [ ] Self-review کردم
- [ ] Comments اضافه کردم
- [ ] Documentation update
- [ ] Tests اضافه کردم
- [ ] تمام تست‌ها pass می‌شوند
- [ ] Breaking changes documented

## مسائل مرتبط
Fixes #123
Related to #456
```

### 3. PR Size

**بهترین اندازه PR**:
- ✅ **Small**: < 200 lines changed
- ⚠️ **Medium**: 200-500 lines
- ❌ **Large**: > 500 lines (باید شکسته شود)

### 4. Draft PRs

برای WIP (Work In Progress):

```bash
# ایجاد Draft PR در GitHub UI
# عنوان: [WIP] Your feature name
```

---

## Review Process

### 1. زمان‌بندی

- **Initial Review**: ظرف 2 روز کاری
- **Follow-up**: ظرف 1 روز کاری

### 2. Review Checklist

Reviewers باید بررسی کنند:
- [ ] کد با requirements مطابقت دارد
- [ ] کد readable و maintainable است
- [ ] تست‌ها کافی و معنادار هستند
- [ ] Performance مناسب است
- [ ] Security vulnerabilities ندارد
- [ ] Documentation کافی است

### 3. پاسخ به Comments

```markdown
# ✅ خوب
> این فانکشن باید async باشد

Good point! Changed to async in abc123

# ❌ بد
> این فانکشن باید async باشد

No.  [بدون توضیح]
```

### 4. Merge Criteria

PR زمانی merge می‌شود که:
- ✅ حداقل **1 approval** از maintainer
- ✅ تمام **CI checks** pass شوند
- ✅ تمام **conversations resolved** شوند
- ✅ بدون **merge conflicts**

---

## سوالات متداول

**Q: PR من چقدر طول می‌کشد تا review شود؟**  
A: معمولاً ظرف 2 روز کاری. اگر urgent است، در PR mention کنید.

**Q: می‌توانم روی چند issue همزمان کار کنم؟**  
A: بله، اما توصیه می‌شود یکی یکی PR بزنید تا review سریع‌تر باشد.

**Q: اگر CI fail شد چه کنم؟**  
A: لاگ‌ها را بررسی کنید، مشکل را fix کنید و push کنید. CI خودکار دوباره اجرا می‌شود.

**Q: breaking change چطور اعلام کنم؟**  
A: در commit message از `!` استفاده کنید و `BREAKING CHANGE:` در footer اضافه کنید.

**Q: اگر با reviewer موافق نبودم؟**  
A: با احترام نظر خود را بیان کنید. اگر توافق حاصل نشد، maintainer دیگری opinion بدهد.

---

## لینک‌های مفید

- [ROADMAP.md](ROADMAP.md) - نقشه راه پروژه
- [DEVELOPMENT.md](DEVELOPMENT.md) - راهنمای setup
- [TESTING.md](TESTING.md) - راهنمای testing
- [docs/architecture.md](docs/architecture.md) - معماری

---

## تشکر

از مشارکت شما سپاسگزاریم! 🙏

هر سوالی دارید، در [Discussions](https://github.com/your-org/multi-agent/discussions) بپرسید.

---

**آخرین به‌روزرسانی**: 2025-11-18  
**Maintainers**: @your-username
