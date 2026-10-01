# راهنمای استقرار Production — Risheh Engage v0.8

این سند Runbook نهایی استقرار قبل از `v1.0` است. هدف این است که Deploy قابل تکرار، قابل بازگشت و قابل بررسی باشد.

## 1) پیش‌نیازها

- Linux VPS یا Container Platform
- Docker + Docker Compose
- PostgreSQL 16+
- Redis 7+
- n8n با Volume پایدار
- Reverse Proxy با TLS
- دامنه‌های جدا یا Routeهای مشخص برای Web/API/n8n
- Backup مقصد خارج از همان دیسک سرور

## 2) Secretهای اجباری

در Production این مقادیر نباید Placeholder باشند:

```env
ENVIRONMENT=production
APP_SECRET_KEY=<random 32+ chars>
N8N_WEBHOOK_SECRET=<random 32+ chars>
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
CORS_ORIGINS=https://engage.example.com
AI_API_BASE_URL=...
AI_API_KEY=...
AI_MODEL=...
```

Settings در Production اگر Secret پیش‌فرض، CORS لوکال یا DB credential توسعه ببیند Boot را Fail می‌کند.

## 3) ترتیب Deploy

```text
Backup
↓
Pull immutable revision/tag
↓
Build images
↓
Database migration
↓
Start API/Worker/Web/n8n
↓
/readiness
↓
Smoke tests
↓
Provider test
↓
Traffic enable
```

نمونه:

```bash
docker compose build
docker compose run --rm migrate
docker compose up -d
SMOKE_API_URL=https://api.example.com \
SMOKE_WEB_URL=https://engage.example.com \
python scripts/production_smoke.py
```

## 4) Migration Rule

- Migration همیشه قبل از API جدید اجرا شود.
- Migrationهای destructive باید Backup تأییدشده داشته باشند.
- قبل از Deploy، `alembic upgrade head` در CI باید موفق باشد.
- Downgrade کورکورانه در Production ممنوع است؛ Rollback باید بر اساس Release Plan باشد.

## 5) Health / Readiness / Metrics

- `/health`: Process زنده است.
- `/ready`: اتصال DB سالم است.
- `/metrics`: متریک Prometheus شامل request count و latency.
- Header `X-Request-ID`: برای Trace کردن درخواست بین Logها.

Alertهای پیشنهادی:

- API 5xx rate بالا
- p95 latency بالا
- DB readiness failure
- Outbox dead-letter > 0
- SLA breach rate
- Provider delivery failure rate

## 6) Backup

```bash
DATABASE_URL='postgresql://...' \
BACKUP_DIR=/var/backups/engage \
./ops/backup.sh
```

Backup باید به Storage دیگری Sync شود. وجود فایل روی همان VPS Disaster Recovery محسوب نمی‌شود.

## 7) Restore Drill

Restore فقط روی Target تأییدشده:

```bash
DATABASE_URL='postgresql://...' \
ALLOW_DESTRUCTIVE_RESTORE=yes \
./ops/restore.sh backups/risheh-engage-....dump
```

بعد:

```bash
alembic upgrade head
python scripts/production_smoke.py
```

حداقل ماهانه یک Restore Drill روی محیط غیرProduction انجام شود.

## 8) n8n

- Editor عمومی نباشد.
- Workflow exports نباید Token داشته باشند.
- Secret boundary باید با `X-Automation-Secret` حفظ شود.
- Provider failure باید Callback/Retry قابل مشاهده داشته باشد.
- n8n Source of Truth نیست.

## 9) Pilot Provider Gate

برای هر Provider قبل از فعال‌شدن برای مشتری:

1. inbound webhook واقعی
2. duplicate webhook
3. outbound send
4. callback
5. invalid credential
6. rate limit
7. timeout/retry
8. opt-out/consent
9. tenant isolation

Telegram اولین Provider مناسب Pilot است. Instagram/WhatsApp تا Live Smoke رسمی Production-ready محسوب نمی‌شوند.

## 10) Rollback

اگر Smoke شکست خورد:

```text
Stop traffic
↓
Keep evidence/logs
↓
Rollback application image
↓
Assess DB migration compatibility
↓
Restore only if required
↓
Run smoke again
```

DB Restore آخرین گزینه است، نه اولین گزینه.

## Definition of Successful Production Deployment

Deploy فقط زمانی موفق است که:

- migration موفق باشد؛
- `/ready` = 200؛
- Smoke Script کامل PASS شود؛
- Outbox Worker فعال باشد؛
- Backup قابل بازیابی وجود داشته باشد؛
- Provider Pilot test موفق باشد؛
- Monitoring و alert owner مشخص باشند.
