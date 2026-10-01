# وضعیت پیاده‌سازی — Risheh Engage

نسخه: `v0.8 — Final Candidate / Production Readiness`

این نسخه Feature Freeze پیشنهادی قبل از Pilot است. تمرکز v0.8 روی **اثبات اجراپذیری، امنیت تنظیمات، Observability، Backup/Restore و Release Gates** است.

## ✅ Product Core تکمیل‌شده

### Content / Automation
- Workspace / Brand / Content lifecycle
- Human approval
- Publication + Idempotency
- PostgreSQL Source of Truth
- Transactional Outbox
- Reliable Worker با lock/retry/backoff/dead-letter
- n8n provider boundary

### Auth / Tenant
- JWT
- Argon2
- Workspace Membership
- Explicit RBAC
- Tenant access guard

### Customer Communication
- Customer / CustomerIdentity
- Conversation / Message
- Inbound deduplication
- Unified Inbox
- Human Handoff
- Outbound Messaging
- Delivery Callback

### LeadOps
- Lead lifecycle
- Lead score
- Follow-up
- stop condition روی Customer reply
- terminal lead guard

### AI / Grounded AI
- Intent Classifier interface
- Structured output validation
- Risk/Confidence policy
- Fail-Closed behavior
- AI Draft persistence
- Human Review/Edit/Approve/Reject
- KnowledgeSource / KnowledgeChunk
- RetrievalEvidence
- No Evidence → Grounded Draft blocked
- Evidence inspection در Review Queue

### Identity / Privacy Foundation
- Identity Verification
- verified-only merge
- merge conflict guards
- Consent scoped by purpose/channel
- Marketing/Sales consent enforcement
- encrypted Provider Credential foundation

### SLA / Customer 360 / Attribution
- First-response SLA tracker
- breach/escalation foundation
- first successful outbound response hook
- Customer 360 read model
- Attribution Touchpoint + summary

### UI
- `/studio`
- `/inbox`
- `/ai-queue`
- `/knowledge`

### Database Migrations
- 0001 Content Lifecycle
- 0002 Auth + Reliable Outbox
- 0003 Customer Communication
- 0004 AI + Outbound + Attribution
- 0005 Grounded AI + Consent + SLA + Credentials + Identity Verification

---

# ✅ v0.8 Finalization اضافه‌شده

## Runtime Safety
- API/Web version `0.8.0`
- Production config validation
- Placeholder/weak secret rejection
- unsafe Production CORS rejection
- development DB credential rejection در Production

## Observability
- `X-Request-ID`
- request count metric
- request latency histogram
- `/metrics`
- `/health`
- `/ready`
- request completion log

## CI / Quality Gate
CI جدید برای اجرای واقعی این مسیر طراحی شده است:

```text
PostgreSQL service
↓
Install
↓
Critical static checks
↓
Alembic upgrade head
↓
Unit/Contract/Integration tests
↓
Next.js production build
↓
Release files gate
```

Integration test جدید:
- وجود Schema بعد از Alembic
- وجود Tableهای حیاتی
- enforce شدن unique constraint واقعی PostgreSQL

## Operational Readiness
- `scripts/production_smoke.py`
- `ops/backup.sh`
- `ops/restore.sh`
- Restore destructive guard
- `docs/PRODUCTION_DEPLOYMENT_FA.md`
- `docs/FINAL_RELEASE_CHECKLIST_FA.md`

## Training v0.8
- `docs/FINALIZATION_GLOSSARY_FA.md`
- `docs/FINALIZATION_TRAINING_FA.md`
- README v0.8 Final Candidate

---

# ⚠️ Evidenceهای باقی‌مانده قبل از v1.0

این موارد عمدتاً نیازمند Runtime/Credential واقعی هستند و نباید بدون Evidence تیک بخورند:

## CI / Runtime
- GitHub Actions باید Job Stepها را واقعاً اجرا کند و سبز شود
- Docker/runtime smoke روی ماشین واقعی
- PostgreSQL integration run واقعی در CI
- Restore Drill واقعی

## Provider Pilot
### Telegram
- inbound live smoke
- outbound live smoke
- duplicate webhook
- invalid token
- timeout/retry/callback

### Instagram / WhatsApp
- Meta webhook verification
- credential lifecycle
- inbound/outbound live smoke
- rate-limit behavior

## Security قبل از Public Launch
- Auth/Webhook rate limiting
- external Secret Manager/KMS + rotation
- PII retention/export/delete workflow
- incident owner/runbook validation

## AI Hardening
- Pilot evaluation dataset
- prompt injection evaluation
- knowledge freshness/versioning
- semantic/vector retrieval در صورت بزرگ‌شدن Knowledge Base

> Semantic retrieval عمداً شرط v0.8 Final Candidate نیست. Retrieval فعلی Evidence-based و deterministic است. برای Knowledge Base بزرگ، Vector retrieval یک ارتقای مهم بعدی است؛ اضافه‌کردن عجولانه آن قبل از Pilot به‌جای Stability توصیه نمی‌شود.

## Analytics
- Conversion entity
- Revenue entity
- Revenue Attribution
- advanced funnel dashboard

این‌ها برای Pilot اولیه الزامی نیستند مگر قرارداد مشتری به آن‌ها وابسته باشد.

---

# Release Gate v0.8

## Repository Gate
- [x] Feature Freeze direction
- [x] Production config guard
- [x] Observability foundation
- [x] PostgreSQL integration test file
- [x] Alembic-in-CI design
- [x] Frontend production build gate
- [x] Smoke script
- [x] Backup script
- [x] Guarded restore script
- [x] Deployment runbook
- [x] Final release checklist
- [x] Final technical glossary/training
- [x] README final candidate

## Evidence Gate
- [ ] GitHub Actions steps execute and pass
- [ ] Production-like Docker smoke
- [ ] Backup + Restore Drill
- [ ] Telegram live provider smoke
- [ ] Pilot Workspace acceptance

---

# تعریف آماده‌بودن برای v1.0

```text
v0.8 Final Candidate
        ↓
CI Green with real steps
        ↓
Production-like Deploy
        ↓
Smoke + Restore Drill
        ↓
Telegram Live Pilot
        ↓
Pilot Acceptance
        ↓
Risheh Engage v1.0
```

**v0.8 از نظر Repository و Release Engineering آخرین مرحله توسعه اصلی است. v1.0 باید با Evidence محیط واقعی اعلام شود، نه صرفاً Merge کد.**
