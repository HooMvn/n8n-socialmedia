# راهنمای آموزشی مرحله نهایی — Risheh Engage v0.8

هدف این مرحله یادگیری «ساخت Feature» نیست؛ یادگیری **تحویل مسئولانه یک محصول واقعی** است.

## فصل 1 — تفاوت Done و Production Ready

یک Feature وقتی Done است که Acceptance Criteria خودش را پاس کند. یک Product وقتی Production Ready است که علاوه بر Featureها، این موارد هم مشخص باشند:

- failure behavior
- security boundary
- migration
- observability
- backup/restore
- rollback
- ownership
- incident response

تمرین: برای Outbound Messaging پنج Failure Mode بنویسید و بگویید هر کدام کجا دیده می‌شوند.

## فصل 2 — CI واقعی

CI باید حداقل این مراحل را اجرا کند:

```text
Checkout
↓
Install
↓
Static Critical Checks
↓
Start PostgreSQL
↓
Alembic Migration
↓
Unit + Contract + Integration Tests
↓
Frontend Production Build
↓
Release Gate
```

### نکته
CI سبز فقط وقتی معتبر است که Jobها و Stepها واقعاً اجرا شده باشند.

تمرین: فرق `workflow failure before steps` و `pytest failure` را توضیح دهید.

## فصل 3 — Migration Engineering

Migration بخشی از Deployment است، نه کار یک‌بار مصرف توسعه‌دهنده.

باید بتوانید پاسخ دهید:

- آیا Migration روی DB خالی کار می‌کند؟
- روی نسخه قبلی Schema چه؟
- آیا lock طولانی ایجاد می‌کند؟
- Rollback application با Schema جدید سازگار است؟
- Backup قبل از تغییر destructive داریم؟

## فصل 4 — Observability

سه ستون پایه:

### Logs
برای رخدادهای جزئی و Context.

### Metrics
برای trend و alert.

### Correlation / Request ID
برای دنبال کردن مسیر Request.

در v0.8 API request count، latency و X-Request-ID دارد.

تمرین: اگر مشتری بگوید «پیام من ارسال نشد»، ترتیب بررسی Log/Outbox/Provider Callback را بنویسید.

## فصل 5 — Backup / Restore

قاعده:

> Backupی که Restore نشده، اثبات‌شده نیست.

تمرین عملی:

1. یک DB آزمایشی بسازید.
2. چند Customer و Conversation ایجاد کنید.
3. Backup بگیرید.
4. DB آزمایشی را پاک کنید.
5. Restore کنید.
6. Smoke Test بزنید.

## فصل 6 — Security Release Gate

قبل از Production:

- secret پیش‌فرض ممنوع
- CORS wildcard ممنوع
- TLS الزامی
- n8n editor private
- credential در workflow export ممنوع
- PII در log بررسی شود
- auth/webhook rate limiting برنامه داشته باشد

در v0.8 Settings در Production برخی Configهای خطرناک را Fail می‌کند.

## فصل 7 — Provider Verification

Adapter آماده بودن با Provider واقعی کار کردن فرق دارد.

برای Telegram/Instagram/WhatsApp باید جداگانه تست شود:

- webhook
- inbound normalization
- duplicate webhook
- outbound delivery
- credential expiry
- rate limit
- callback
- retry
- consent

## فصل 8 — Pilot Engineering

Pilot یعنی استفاده محدود و کنترل‌شده با Customer واقعی.

برای Pilot باید مشخص باشد:

- Workspace Pilot کدام است؟
- مسئول Incident کیست؟
- چه کانالی فعال است؟
- چه Featureهایی disabled هستند؟
- چه KPIهایی اندازه‌گیری می‌شوند؟
- شرایط توقف Pilot چیست؟

## فصل 9 — Release Decision

Release decision نباید بر اساس «فکر کنم آماده است» باشد.

از `FINAL_RELEASE_CHECKLIST_FA.md` استفاده کنید.

### Gate آموزشی نهایی

فرد قبل از Deploy باید بدون مراجعه به فایل بتواند جواب دهد:

1. Health و Readiness چه فرقی دارند؟
2. Smoke و E2E چه فرقی دارند؟
3. چرا Migration بخشی از CI است؟
4. چرا Backup بدون Restore Drill کافی نیست؟
5. Request ID چه مشکلی حل می‌کند؟
6. چرا n8n Source of Truth نیست؟
7. Fail-Closed یعنی چه؟
8. Provider live smoke چرا جدا از Unit Test است؟
9. RPO و RTO چه هستند؟
10. چه زمانی v0.8 را می‌توان v1.0 نامید؟

اگر پاسخ‌ها مبهم باشند، Deploy Production نباید انجام شود.
