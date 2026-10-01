# Runbook ارسال پیام Outbound — Risheh Engage v0.6

این سند مسیر واقعی ارسال پاسخ AI-approved یا Human-written را از Backend تا Telegram توضیح می‌دهد.

---

## معماری

```text
AI Draft Approved / Human Reply
            ↓
     OutboundMessage
            ↓
     OutboxEvent
            ↓
     Reliable Worker
            ↓
       n8n Webhook
            ↓
 Resolve Delivery Context
            ↓
     Channel Adapter
            ↓
        Telegram
            ↓
       Callback API
            ↓
 Outbound Status + Message
```

---

# 1. Environment

حداقل:

```env
N8N_OUTBOUND_WEBHOOK_URL=http://n8n:5678/webhook/risheh-engage-outbound
RISHEH_API_BASE_URL=http://api:8000
RISHEH_AUTOMATION_SECRET=...
TELEGRAM_BOT_TOKEN=...
```

`RISHEH_AUTOMATION_SECRET` باید با `N8N_WEBHOOK_SECRET` Backend یکی باشد.

---

# 2. Workflow

فایل Import:

```text
automation/workflows/telegram_outbound_v1.json
```

نام:

```text
ENGAGE__OUTBOUND__TELEGRAM__V1
```

پس از Import:

1. Environmentها را تنظیم کنید.
2. Workflow را Activate کنید.
3. Production Webhook URL را در `N8N_OUTBOUND_WEBHOOK_URL` قرار دهید.

---

# 3. Event Contract

Worker Event زیر را به n8n می‌فرستد:

```json
{
  "event_type": "message.outbound.requested",
  "aggregate_type": "outbound_message",
  "aggregate_id": "OUTBOUND_UUID",
  "idempotency_key": "outbox:...",
  "payload": {}
}
```

n8n نباید Customer target را حدس بزند.

---

# 4. Delivery Context

n8n این Endpoint را صدا می‌زند:

```http
GET /api/v1/automation/outbound/{outbound_id}/delivery-context
X-Automation-Secret: ...
```

Backend بر اساس:

```text
workspace_id
customer_id
channel
```

`CustomerIdentity` مناسب را Resolve می‌کند.

نمونه پاسخ:

```json
{
  "channel": "telegram",
  "target_external_user_id": "12345678",
  "body": "سلام ...",
  "idempotency_key": "ai-draft:..."
}
```

### اصل مهم

`Customer.id` هرگز Telegram Chat ID نیست.

---

# 5. Telegram Send

Adapter فعلی:

```text
POST https://api.telegram.org/bot<TOKEN>/sendMessage
```

Body:

```json
{
  "chat_id": "target_external_user_id",
  "text": "body"
}
```

---

# 6. Callback

بعد از ارسال:

```http
POST /api/v1/automation/outbound/callback
X-Automation-Secret: ...
```

نمونه:

```json
{
  "outbound_message_id": "...",
  "idempotency_key": "...",
  "status": "sent",
  "external_message_id": "901"
}
```

Backend:

- وضعیت Outbound را تغییر می‌دهد.
- `sent_at` را ثبت می‌کند.
- Message رسمی outbound در Conversation می‌سازد.
- اگر AI Draft مبنا بوده `author_type=ai` ثبت می‌شود.
- اگر پاسخ انسانی بوده `author_type=human` ثبت می‌شود.

---

# 7. Statusها

```text
queued
 ↓
sent
 ↓
delivered
```

Failure:

```text
queued → failed
```

Cancel:

```text
queued → cancelled
```

Telegram Bot API در این Workflow فعلاً Delivery Receipt واقعی `delivered` نمی‌دهد؛ بنابراین موفقیت `sendMessage` به `sent` نگاشت می‌شود.

---

# 8. Retry

Retry در Worker انجام می‌شود:

- Lock
- `FOR UPDATE SKIP LOCKED`
- Exponential Backoff
- Max Attempts
- Dead Letter

n8n نباید Business State را Retry کند.

---

# 9. Idempotency

Outbound دارای:

```text
workspace_id + idempotency_key
```

Unique Constraint است.

اما توجه:

Telegram `sendMessage` exactly-once تضمین نمی‌کند.

سناریو:

```text
Telegram success
↓
Callback/network failure
↓
Worker retry
↓
Potential duplicate send
```

برای Production سخت‌گیرانه باید Provider Operation Ledger / Dedup strategy اضافه شود.

---

# 10. تست دستی

## Human reply

از `/inbox`:

1. Conversation را باز کنید.
2. متن Human Reply بنویسید.
3. Send را بزنید.
4. Outbound باید `queued` شود.
5. Worker Event را تحویل دهد.
6. Telegram پیام را دریافت کند.
7. Callback وضعیت را `sent` کند.

## AI reply

1. `AI Classify`
2. `Generate AI Draft`
3. `/ai-queue`
4. متن را بررسی/ویرایش کنید.
5. Approve
6. Outbound باید ساخته شود.
7. مسیر Delivery را بررسی کنید.

---

# 11. Failure Test

### Bot token اشتباه

انتظار:

```text
n8n fails
→ Worker receives non-2xx
→ Outbox retry/backoff
→ eventually dead_letter
```

### CustomerIdentity وجود ندارد

Delivery Context باید `409` بدهد.

سیستم نباید Chat ID حدس بزند.

---

# 12. Production Gate

قبل از Production:

- Credential per Workspace
- Provider Operation Ledger
- Delivery metrics
- Alert روی Dead Letter
- Rate limit per Provider
- Consent/Opt-out
- PII policy
- Telegram live smoke
- Integration tests
- Instagram/WhatsApp adapter-specific contracts
