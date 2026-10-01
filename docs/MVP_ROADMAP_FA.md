# Roadmap نسخه MVP — Risheh Engage

هدف MVP اثبات یک حلقه کامل است، نه ساخت تمام قابلیت‌های Social Media Management.

## North Star اولیه

**Qualified Conversations Generated per Active Workspace**

## حلقه‌ای که باید End-to-End کار کند

```text
Create Content
→ Approve
→ Publish
→ Receive Interaction
→ Create/Resolve Customer
→ Create Lead
→ Follow-up
→ Measure Result
```

---

# Phase 0 — Architecture & Contracts

## خروجی

- Domain boundaries
- Initial ER model
- API conventions
- Event envelope
- Error contract
- RBAC matrix
- Integration interface contracts
- Architecture Decision Records برای تصمیم‌های مهم

## Gate

کدنویسی Featureهای اصلی قبل از مشخص شدن contractهای بالا آغاز نمی‌شود.

---

# Phase 1 — Foundation

## Backend

- FastAPI skeleton
- PostgreSQL
- Alembic migrations
- Workspace model
- User/Membership
- RBAC
- Audit foundation
- Health/readiness endpoints
- structured logging

## Frontend

- Next.js shell
- authentication flow
- workspace switcher
- navigation
- loading/error/empty primitives

## Infrastructure

- Docker Compose development environment
- PostgreSQL
- Redis
- n8n
- API
- Web

## Gate

- tenant isolation test
- migrations reproducible
- secrets خارج repository
- `/health` و `/ready` قابل استفاده

---

# Phase 2 — Brand Brain + ContentOps

## Featureها

- Brand Profile
- Knowledge Sources پایه
- Content Item
- AI Draft generation
- platform variants
- Content Calendar
- Approval
- publish request
- Telegram publishing
- Instagram adapter interface + implementation بر اساس API مجاز

## Gate

کاربر بتواند:

1. Brand را تنظیم کند.
2. Draft بسازد.
3. آن را Edit کند.
4. Approve کند.
5. Schedule/Publish کند.
6. status انتشار را ببیند.

Failure انتشار باید در UI قابل مشاهده و replay باشد.

---

# Phase 3 — Conversation Hub

## Featureها

- inbound webhook boundary
- Customer
- CustomerIdentity
- Conversation
- Message
- Unified Inbox
- assignment
- intent classification
- AI reply draft
- human send

## Gate

یک پیام واقعی ورودی باید:

1. Deduplicate شود.
2. Customer مناسب را resolve/create کند.
3. در Inbox نمایش داده شود.
4. پاسخ اپراتور را ارسال کند.
5. Audit و delivery status داشته باشد.

---

# Phase 4 — LeadOps + Follow-up

## Featureها

- Create lead from conversation
- source attribution
- simple pipeline
- lead owner
- follow-up scheduling
- reminders
- stop conditions
- lead activity timeline

## Gate

هیچ Lead باز نباید بدون `owner` یا `next_action` در وضعیت عملیاتی رها شود، مگر policy مشخص داشته باشد.

---

# Phase 5 — Analytics

## داشبورد پایه

### Content

- drafts
- published
- publishing failures
- approval time

### Inbox

- open conversations
- first response time
- human handoffs

### Leads

- created
- qualified
- won/lost
- overdue follow-ups

### Funnel

```text
Published Content
→ Conversation
→ Lead
→ Qualified
→ Won
```

## Gate

Metricها از eventهای واقعی سیستم ساخته می‌شوند، نه داده نمایشی و دستی.

---

# Phase 6 — SaaS Hardening

بعد از اثبات حلقه MVP:

- advanced onboarding
- plan/feature entitlement
- billing integration
- usage limits
- retention policies
- data export/delete
- workspace invitations
- provider health dashboard
- backup/restore runbook
- rate limiting
- production observability

---

# بعد از MVP

اولویت‌ها بر اساس داده واقعی انتخاب می‌شوند؛ نه صرفاً جذابیت Feature.

Candidateها:

- WhatsApp adapter
- Advanced Comment-to-DM
- Repurposing Engine
- Campaign Builder
- Customer 360 merge
- Advanced AI routing
- Content Intelligence
- Competitor monitoring
- Revenue attribution
- Vertical templates

---

# چیزی که فعلاً نباید بسازیم

- full enterprise CRM
- video editor کامل
- Canva replacement
- generic workflow builder برای customer
- microservices
- multi-region deployment
- autonomous sales bot بدون human controls
- ده‌ها social connector قبل از اثبات دو connector اول

---

# Sprint Prioritization Formula

هر Feature با این معیارها امتیاز می‌گیرد:

| معیار | سؤال |
|---|---|
| User Pain | آیا درد واقعی و مکرر را حل می‌کند؟ |
| Revenue | آیا قابلیت فروش/Retention را بهتر می‌کند؟ |
| Core Loop | آیا Content→Conversation→Conversion را تقویت می‌کند؟ |
| Risk | ریسک امنیت/Provider/Policy چقدر است؟ |
| Complexity | هزینه ساخت و نگهداری چقدر است؟ |
| Learning | آیا داده‌ای تولید می‌کند که تصمیم بعدی را بهتر کند؟ |

---

# MVP Release Gate

نسخه اولیه فقط زمانی Release Candidate محسوب می‌شود که:

- [ ] tenant isolation تست شده باشد.
- [ ] duplicate webhook باعث duplicate entity نشود.
- [ ] publish failure قابل retry باشد.
- [ ] inbound/outbound message قابل audit باشد.
- [ ] human approval واقعاً enforce شود.
- [ ] AI provider failure محصول را از کار نیندازد.
- [ ] follow-up stop condition تست شده باشد.
- [ ] backup database تعریف شده باشد.
- [ ] secret scanning فعال باشد.
- [ ] حداقل یک مسیر E2E واقعی Content→Lead اجرا شده باشد.
- [ ] هیچ mock/fake metric در production dashboard نمایش داده نشود.
