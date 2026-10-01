# مسیر آموزشی تیم — Risheh Engage v0.6

این مسیر اجباری است تا توسعه‌دهنده قبل از گرفتن Task، **مدل ذهنی محصول، Domain، AI Safety و Delivery Architecture** را بفهمد.

---

## مرحله 0 — Product Model

مطالعه:

1. `README.md`
2. `docs/PRODUCT_PRINCIPLES_FA.md`
3. `docs/PROJECT_GUIDE_FA.md`

باید بتوانید این چرخه را توضیح دهید:

```text
Content
→ Conversation
→ Customer
→ Intent
→ AI/Human
→ Outbound
→ Lead
→ Follow-up
→ Conversion
→ Learning
```

---

## مرحله 1 — Architecture / Source of Truth

مطالعه:

- `docs/ARCHITECTURE_FA.md`
- `docs/DOMAIN_MODEL_FA.md`
- `docs/TECHNICAL_GLOSSARY_FA.md`

مفاهیم:

`Domain`, `Source of Truth`, `Modular Monolith`, `Event-driven`, `Outbox`, `Idempotency`, `Multi-tenancy`, `Adapter`.

تمرین:

```text
AI Draft Approved
→ OutboundMessage
→ OutboxEvent
→ Worker
→ n8n
→ Telegram
→ Callback
```

برای هر مرحله Owner State را مشخص کنید.

---

## مرحله 2 — Backend

باید بلد باشید:

- Python typing
- FastAPI Dependency Injection
- Pydantic
- Async SQLAlchemy
- REST API Design
- Error contract
- Authentication / Authorization
- RBAC

تمرین: یک Endpoint طراحی کنید و بگویید Validation، Tenant Scope و Permission کجا enforce می‌شود.

---

## مرحله 3 — PostgreSQL / Migration

مفاهیم:

- PK / FK
- Unique Constraint
- Composite Unique
- Index
- Transaction
- Alembic
- Locking
- `FOR UPDATE SKIP LOCKED`

مدل v0.6 را رسم کنید:

```text
Customer
├── CustomerIdentity
├── Conversation
│   ├── Message
│   ├── AIDraft
│   └── OutboundMessage
├── Lead
│   └── FollowUp
└── AttributionTouchpoint
```

---

## مرحله 4 — Security

مطالعه:

- `SECURITY.md`
- `docs/PHASE_1_SECURITY_RELIABILITY_FA.md`

موضوعات:

- JWT
- Argon2
- RBAC
- Least Privilege
- Secret Management
- Webhook Authentication
- PII
- Tenant Isolation

اصل: UUID یا Workspace ID به‌تنهایی Permission نیست.

---

## مرحله 5 — n8n / Channel Adapter

مطالعه:

- `automation/README.md`
- `automation/PUBLISH_PIPELINE_FA.md`
- `automation/TELEGRAM_PROVIDER_RUNBOOK_FA.md`
- `automation/TELEGRAM_INBOUND_RUNBOOK_FA.md`
- `automation/OUTBOUND_RUNBOOK_FA.md`

باید بدانید:

- n8n Orchestrator است، نه Database.
- Channel Adapter باید Provider-specific data را از Domain جدا نگه دارد.
- Delivery Context باید Target Identity را از Backend بگیرد.

---

## مرحله 6 — Customer Communication

مطالعه:

- `docs/VERTICAL_SLICE_02_CUSTOMER_COMMUNICATION_FA.md`
- `docs/CUSTOMER_COMMUNICATION_GLOSSARY_FA.md`

باید فرق این‌ها را بدانید:

- Customer vs Identity
- Conversation vs Message
- Intent vs Sentiment
- Customer vs Lead
- Follow-up vs Outbound Message
- Human Handoff vs Assignment

تمرین: Inbound Message را دوبار ارسال کنید و Deduplication را بررسی کنید.

---

## مرحله 7 — AI Customer Communication

مطالعه اجباری:

- `docs/AI_CUSTOMER_COMMUNICATION_GUIDE_FA.md`
- `docs/AI_OUTBOUND_GLOSSARY_FA.md`

مفاهیم:

- Intent Classifier
- Structured Output
- Confidence
- Deterministic Policy
- Guardrail
- Fail-Closed
- Human-in-the-loop
- Evaluation
- Prompt Injection

اصل:

```text
AI infers
Policy decides
Domain changes state
Human controls risky actions
```

تمرین:

1. پیام کم‌ریسک را Classify کنید.
2. پیام Refund را با Confidence 99 تست کنید.
3. توضیح دهید چرا باز هم Human Required است.
4. Provider را خاموش کنید و Fail-Closed را ببینید.

---

## مرحله 8 — AI Draft / Review Queue

مسیر:

```text
Inbound Message
→ Intent
→ Risk Policy
→ AI Draft
→ Review Queue
→ Edit / Approve / Reject
```

تمرین:

- Draft بسازید.
- متن را Edit کنید.
- Approve کنید.
- بررسی کنید Outbound فقط بعد از Approval ساخته شود.
- Draft دیگری را Reject کنید و مطمئن شوید Outbound ساخته نمی‌شود.

---

## مرحله 9 — Outbound Delivery

مفاهیم:

- Outbound Message
- Delivery Context
- Idempotency
- At-least-once
- Sent vs Delivered
- Callback
- Provider Operation Ledger

تمرین Human:

```text
/inbox
→ Human Reply
→ Outbound queued
→ Outbox
→ n8n
→ Telegram
→ callback
```

توضیح دهید چرا `Customer.id` نباید Telegram Chat ID باشد.

---

## مرحله 10 — Customer 360 / Attribution

مطالعه:

- `docs/AI_OUTBOUND_GLOSSARY_FA.md`

باید بدانید:

- Customer 360 یک Read Model است.
- Touchpoint چیست.
- Content Attribution چیست.
- First-touch / Last-touch / Multi-touch چه تفاوتی دارند.

تمرین: برای یک Customer حداقل 3 Touchpoint با دو Channel ثبت کنید و Timeline منطقی بسازید.

---

## مرحله 11 — Follow-up Safety

Stop Conditionهای فعلی:

- Customer reply → pending follow-ups cancel
- Manual stop
- Closed lead → follow-up جدید ممنوع

آینده:

- Opt-out
- Purchase completed
- Appointment completed
- Consent rules

تمرین: Lead بسازید، Follow-up بسازید، سپس Inbound Reply بفرستید و Cancel شدن را بررسی کنید.

---

## مرحله 12 — Frontend / UX

مسیرها:

- `/studio`
- `/inbox`
- `/ai-queue`

باید Loading، Empty، Error، Pending Review، Waiting Human و Delivery State را طراحی کنید.

---

## مرحله 13 — Testing

ترتیب:

1. Pure Policy Test
2. Schema Contract
3. AI fail-closed test
4. API Test
5. PostgreSQL Integration Test
6. Worker/Outbox Test
7. n8n Contract Test
8. E2E

Failureهای اجباری:

- duplicate webhook
- cross-tenant request
- low-confidence intent
- sensitive intent
- AI provider unavailable
- missing CustomerIdentity
- duplicate outbound idempotency key
- provider success + callback failure
- dead-letter

---

## مرحله 14 — Observability

باید بلد باشید:

- Structured Log
- Correlation ID
- Metric
- Trace
- Retry / Backoff / DLQ
- AI latency/error rate
- Draft acceptance rate
- Handoff rate
- Delivery failure rate

---

# Gate ورود به Task اصلی v0.6

بدون مراجعه به سند باید پاسخ دهید:

1. AI Draft با Message چه فرقی دارد؟
2. Confidence چرا Permission نیست؟
3. Deterministic Policy چرا بیرون LLM است؟
4. Fail-Closed چیست؟
5. Human Review کجا enforce می‌شود؟
6. OutboundMessage چه زمانی ساخته می‌شود؟
7. Delivery Context چیست؟
8. Customer ID با Provider Identity چه فرقی دارد؟
9. At-least-once چه Duplicate Riskی دارد؟
10. Customer 360 Read Model چیست؟
11. Attribution Touchpoint چیست؟
12. چرا Customer Reply باید Follow-up را متوقف کند؟
13. Prompt Injection چیست؟
14. n8n مالک چه چیزی نیست؟
15. چه چیزهایی هنوز Production Gate هستند؟

اگر پاسخ‌ها مبهم‌اند، Task Production نباید شروع شود.
