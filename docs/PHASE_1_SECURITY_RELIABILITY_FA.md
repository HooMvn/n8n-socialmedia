# فاز امنیت، قابلیت اطمینان و اولین Provider — Risheh Engage v0.4

این سند توضیح می‌دهد چرا و چگونه سه جزء زیر به Vertical Slice 01 اضافه شده‌اند:

1. Authentication + RBAC
2. Reliable Outbox Worker
3. Telegram Provider Adapter در n8n

---

## 1) Authentication

### چرا؟
قبل از این فاز، API می‌توانست Workspace و Content را بدون هویت واقعی کاربر دریافت کند. این برای Prototype قابل قبول است اما برای SaaS خطرناک است.

### مدل فعلی

```text
Register / Login
      ↓
JWT Access Token
      ↓
Current User
      ↓
Workspace Membership
      ↓
Role Gate
      ↓
Business Action
```

### Password Security
پسورد خام هرگز ذخیره نمی‌شود. از Argon2 از طریق `pwdlib` استفاده می‌شود.

### JWT
توکن شامل `sub`, `email`, `iss`, `aud`, `iat`, `exp` است. کلید امضا باید در Production یک Secret قوی و خارج از Repository باشد.

### Roleها

- `owner`: مالک Workspace
- `admin`: مدیریت عملیاتی Workspace
- `editor`: Brand و Content editing
- `reviewer`: Approval / Rejection / Publish
- `analyst`: برای Analytics فاز بعد
- `viewer`: فقط مشاهده

نقش‌ها عمداً به‌صورت Rank پیاده نشده‌اند. Permission هر Action با Role Set صریح کنترل می‌شود؛ چون Reviewer الزاماً Editor نیست.

### اصل Tenant Isolation
وجود UUID یک Workspace در URL به‌معنای دسترسی نیست. کاربر باید Membership همان Workspace را داشته باشد.

---

## 2) Reliable Outbox Worker

### مشکل Polling ساده
اگر چند Worker همزمان Event یکسان را بردارند یا Worker وسط ارسال Crash کند، ممکن است Event گم یا چندبار اجرا شود.

### راه‌حل
Worker از این الگو استفاده می‌کند:

```text
SELECT eligible events
      ↓
FOR UPDATE SKIP LOCKED
      ↓
status = processing
locked_at / locked_by
      ↓
POST to n8n webhook
      ↓
Success → delivered
Failure → retry/backoff
      ↓
max attempts reached
      ↓
dead_letter
```

### چرا `SKIP LOCKED`؟
چند Worker می‌توانند همزمان کار کنند بدون اینکه یک Event را همزمان claim کنند یا منتظر Lock یکدیگر بمانند.

### Stale Lock Recovery
اگر Worker بعد از claim کردن Crash کند، `locked_at` برای همیشه Event را زندانی نمی‌کند. بعد از `OUTBOX_LOCK_SECONDS` Worker دیگر می‌تواند Event را reclaim کند.

### Retry
Backoff نمایی است و سقف آن 300 ثانیه است.

### Dead Letter Queue
بعد از `OUTBOX_MAX_ATTEMPTS` Event به `dead_letter` می‌رود. این Event نباید خودکار بی‌نهایت retry شود؛ نیاز به مشاهده، تشخیص علت و replay کنترل‌شده دارد.

### Delivery Semantics
این سیستم **at-least-once delivery** دارد، نه exactly-once. بنابراین تمام مصرف‌کننده‌ها باید Idempotent طراحی شوند.

---

## 3) چرا Worker مستقیم Telegram را صدا نمی‌زند؟

معماری محصول این است:

```text
FastAPI / Domain
      ↓
PostgreSQL Outbox
      ↓
Outbox Worker
      ↓
n8n
      ↓
Provider Adapter
      ↓
Telegram / Instagram / ...
```

اگر Worker مستقیماً Telegram را صدا بزند، Backend کم‌کم به Integrationهای خارجی گره می‌خورد. n8n مرز orchestration و provider integration باقی می‌ماند.

---

## 4) Telegram Provider Adapter

Workflow قابل Import:

`automation/workflows/telegram_publish_v1.json`

نام استاندارد:

`ENGAGE__PUBLISH__TELEGRAM__V1`

### Environment لازم

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_DEFAULT_CHAT_ID`
- `RISHEH_API_BASE_URL`
- `RISHEH_AUTOMATION_SECRET`

### جریان

```text
Outbox Worker
   ↓
Webhook n8n
   ↓
Validate secret + event contract
   ↓
Telegram sendMessage
   ↓
Publication Callback
   ↓
FastAPI changes Publication + Content state
```

### Contract Event
Event مورد انتظار:

`content.publish.requested`

Payload شامل:

- `publication_id`
- `content_id`
- `workspace_id`
- `platform`
- `text`
- `idempotency_key`

### نکته مهم Telegram
Telegram `sendMessage` کلید Idempotency بومی ندارد. اگر پیام در Telegram موفق شود اما Callback به Backend شکست بخورد، retry بعدی بالقوه می‌تواند Duplicate بسازد. برای Production سخت‌گیرانه باید یکی از این الگوها اضافه شود:

- Provider operation ledger
- Dedup store در Redis/PostgreSQL
- Controlled reconciliation

تا قبل از آن، semantics را exactly-once فرض نکنید.

---

## 5) Studio جدید

`/studio` اکنون این مسیر را اجرا می‌کند:

```text
Register/Login
↓
JWT
↓
Create Workspace (Owner Membership)
↓
Brand
↓
Draft
↓
Review
↓
Approve
↓
Publish
↓
Outbox
↓
Worker → n8n
```

یعنی Demo از این فاز به بعد Anonymous نیست.

---

## 6) Migration

Migration جدید:

`0002_auth_and_outbox_reliability.py`

اضافه می‌کند:

- users
- memberships
- workspace_role enum
- outbox attempt_count
- next_attempt_at
- locked_at
- locked_by
- last_error
- dead_lettered_at
- dead_letter status

---

## 7) تست‌های ضروری

حداقل Contractهای این فاز:

- password hash != password
- valid password verifies
- invalid password fails
- JWT ساخته می‌شود
- نقش‌ها مستقل هستند
- backoff سقف دارد
- Tenant Membership باید روی APIهای Workspace enforce شود
- Publish بدون Reviewer/Admin/Owner رد شود
- Worker retry و DLQ در integration test دیتابیس بررسی شود

دو مورد آخر نیازمند Integration Test واقعی PostgreSQL هستند و باید در CI سالم اجرا شوند.

---

## 8) Production Gate باقی‌مانده

قبل از Production عمومی هنوز این موارد الزامی‌اند:

- Refresh token / session revocation strategy
- Rate limiting روی login/register
- Brute-force protection
- Email verification / password reset
- Admin membership management API
- Secrets manager
- Structured audit log
- Provider credential lifecycle per Workspace
- Outbox metrics + alerting
- Dead-letter replay command/API
- Telegram duplicate mitigation
- Green CI + Docker runtime smoke

---

## 9) تعریف Done این فاز

فاز v0.4 زمانی Done محسوب می‌شود که:

- User بتواند Register/Login کند
- Workspace بدون Auth ساخته نشود
- Creator خودکار Owner شود
- Tenant access بدون Membership رد شود
- Edit/Review permissions از هم جدا باشند
- Worker چند نمونه‌ای Event را duplicate-claim نکند
- Worker Failure را retry کند
- Event خراب به DLQ برسد
- Telegram workflow قابل Import باشد
- Callback Publication state را به‌روزرسانی کند
- Studio با Bearer Token کار کند
- Migration از دیتابیس خالی بالا بیاید
- CI واقعی تست‌ها را اجرا کند

تا زمانی که CI blocker Issue #3 حل نشده، مورد آخر تأییدشده نیست.
