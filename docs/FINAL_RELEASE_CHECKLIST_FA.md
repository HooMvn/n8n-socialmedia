# چک‌لیست نهایی Release — Risheh Engage

این فایل Gate رسمی عبور از `v0.8` به `v1.0` است. هیچ موردی فقط به‌خاطر «احتمالاً درست است» تیک نمی‌خورد.

## A. Build / CI
- [ ] GitHub Actions واقعاً Stepها را اجرا کند.
- [ ] API critical lint PASS.
- [ ] Alembic migration روی PostgreSQL واقعی PASS.
- [ ] Unit/contract tests PASS.
- [ ] PostgreSQL integration tests PASS.
- [ ] Next.js production build PASS.
- [ ] Release-gate job PASS.

## B. Runtime
- [ ] `/health` = 200
- [ ] `/ready` = 200
- [ ] `/metrics` قابل Scrape
- [ ] `X-Request-ID` روی Response
- [ ] Worker در حال Poll
- [ ] Dead-letter monitoring مشخص
- [ ] Web Home/Inbox/AI Queue/Knowledge load شوند

## C. Database
- [ ] `alembic upgrade head` روی DB خالی PASS
- [ ] Upgrade روی snapshot نزدیک Production PASS
- [ ] Unique/idempotency constraints تست شوند
- [ ] Backup قبل از Release ساخته شود
- [ ] Restore Drill روی محیط غیرProduction PASS

## D. Security
- [ ] Production با Secretهای placeholder Boot نشود
- [ ] TLS فعال
- [ ] CORS فقط Originهای لازم
- [ ] DB عمومی نباشد
- [ ] n8n editor عمومی نباشد
- [ ] Credential خام در API/Log/Workflow export نباشد
- [ ] PII logging review انجام شود
- [ ] Rate limiting برای Auth/Webhook قبل از Public Launch فعال شود
- [ ] Key rotation plan ثبت شود

## E. AI / RAG
- [ ] AI بدون Config صحیح Fail-Closed
- [ ] Sensitive intent → Human Required
- [ ] Grounded Draft بدون Evidence Block شود
- [ ] Reviewer Evidence را ببیند
- [ ] Prompt injection test set اجرا شود
- [ ] Evaluation dataset حداقل Pilot آماده شود
- [ ] AI acceptance/edit/reject metrics قابل استخراج باشد

## F. Customer / Messaging
- [ ] Inbound dedup تست شود
- [ ] CustomerIdentity isolation تست شود
- [ ] Verified merge conflict test شود
- [ ] Marketing بدون Consent Block شود
- [ ] Opt-out مسیر Outbound را متوقف کند
- [ ] Human Reply و AI-approved Reply هر دو Outbound بسازند
- [ ] Delivery Callback idempotent باشد
- [ ] Follow-up بعد از Customer Reply متوقف شود

## G. Provider Pilot
### Telegram
- [ ] inbound live
- [ ] outbound live
- [ ] duplicate update
- [ ] invalid token
- [ ] timeout/retry
- [ ] callback

### Instagram
- [ ] webhook verification
- [ ] inbound live
- [ ] outbound live در Scope مجاز API
- [ ] credential expiry/refresh

### WhatsApp
- [ ] webhook verification
- [ ] inbound live
- [ ] outbound live
- [ ] template/session rules بررسی شود

## H. Operations
- [ ] Owner برای Incident مشخص
- [ ] Backup schedule
- [ ] Backup off-server copy
- [ ] Monitoring/alerts
- [ ] Log retention
- [ ] Incident runbook
- [ ] Rollback runbook
- [ ] Provider status check procedure

## I. Product Acceptance
- [ ] Content → Publish واقعی
- [ ] Inbound → Customer → Conversation
- [ ] AI classify → Grounded Draft → Review
- [ ] Approved/Human Reply → Outbound → Delivery
- [ ] Conversation → Lead → Follow-up
- [ ] Customer 360 قابل مشاهده
- [ ] Attribution touchpoint ثبت می‌شود
- [ ] هیچ Fake Production Metric وجود ندارد

# تصمیم Release

فقط وقتی همه Gateهای ضروری Pilot سبز شدند:

```text
v0.8 Final Candidate
        ↓
Pilot Deployment
        ↓
Live Provider Smoke
        ↓
Pilot Acceptance
        ↓
Risheh Engage v1.0
```

`v1.0` یعنی نسخه قابل ارائه به مشتری Pilot؛ نه پایان توسعه محصول.
