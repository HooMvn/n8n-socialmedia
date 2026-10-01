# راهنمای n8n — Publish Pipeline

این سند قرارداد بین Backend و n8n را برای اولین Vertical Slice توضیح می‌دهد.

## اصل معماری

n8n **System of Record نیست**. n8n فقط Orchestrator است.

```text
PostgreSQL = حقیقت Business State
FastAPI    = Business Rules + API Contract
n8n        = Integration / Orchestration Runtime
Provider   = Telegram / Instagram / LinkedIn / ...
```

Workflow نباید مستقیم به جدول‌های Business بنویسد.

## ورودی Workflow

n8n رویدادهای Pending را از Endpoint زیر می‌گیرد:

```http
GET /api/v1/automation/outbox?limit=20
X-Automation-Secret: <N8N_WEBHOOK_SECRET>
```

در Docker Network:

```text
http://api:8000/api/v1/automation/outbox
```

نمونه Event:

```json
{
  "id": "event-uuid",
  "workspace_id": "workspace-uuid",
  "event_type": "content.publish.requested",
  "aggregate_type": "publication",
  "aggregate_id": "publication-uuid",
  "idempotency_key": "outbox:publish-key",
  "payload_json": "{...}"
}
```

`payload_json` باید Parse شود و شامل این Context است:

```json
{
  "event_type": "content.publish.requested",
  "workspace_id": "...",
  "publication_id": "...",
  "content_id": "...",
  "platform": "telegram",
  "text": "...",
  "idempotency_key": "..."
}
```

## Workflow پیشنهادی

```text
Schedule Trigger
      ↓
GET Pending Outbox
      ↓
Loop Over Events
      ↓
Parse payload_json
      ↓
Switch(platform)
 ┌────┼────────────┐
Telegram Instagram LinkedIn
   ↓       ↓          ↓
Adapter  Adapter     Adapter
 └────┬───────────────┘
      ↓
POST Publication Callback
      ↓
ACK Outbox
```

## ترتیب صحیح Callback و ACK

### موفق

1. Provider درخواست انتشار را قبول می‌کند.
2. n8n `POST /publications/callback` با `published` می‌فرستد.
3. Backend وضعیت Publication و Content را Update می‌کند.
4. فقط بعد از موفقیت callback، Outbox با `delivered=true` ACK می‌شود.

### شکست Provider

1. Provider خطا می‌دهد.
2. n8n callback با `failed`, `error_code`, `error_message` می‌فرستد.
3. Backend Content را `failed` می‌کند.
4. Outbox می‌تواند delivered شود چون Event پردازش شده و نتیجه Business ثبت شده است.

### شکست موقت شبکه قبل از ثبت نتیجه

Outbox را ACK نکنید. Event باید برای Retry باقی بماند.

## Callback

```http
POST /api/v1/publications/callback
X-Automation-Secret: <N8N_WEBHOOK_SECRET>
Content-Type: application/json
```

موفق:

```json
{
  "publication_id": "uuid",
  "idempotency_key": "publish-key",
  "status": "published",
  "external_id": "provider-id",
  "external_url": "https://...",
  "error_code": null,
  "error_message": null
}
```

ناموفق:

```json
{
  "publication_id": "uuid",
  "idempotency_key": "publish-key",
  "status": "failed",
  "external_id": null,
  "external_url": null,
  "error_code": "RATE_LIMITED",
  "error_message": "Provider rejected the request"
}
```

## ACK

```http
POST /api/v1/automation/outbox/ack
X-Automation-Secret: <N8N_WEBHOOK_SECRET>
Content-Type: application/json
```

```json
{
  "event_id": "uuid",
  "delivered": true,
  "error_message": null
}
```

## Idempotency

سه سطح Idempotency داریم:

1. UI/API Command: `PublishRequest.idempotency_key`
2. Publication: Unique constraint روی همان key
3. Outbox: `outbox:<publish-key>`

Provider Adapter هم در صورت پشتیبانی Provider باید idempotency را رعایت کند.

## Credential Rule

ممنوع:

```text
Token داخل Workflow JSON
Secret داخل GitHub
Credential داخل Set Node
```

مجاز:

- n8n Credentials
- Environment Secret
- Secret Manager در محیط Production

## Provider Adapter Contract

هر Adapter باید فقط این Interface منطقی را پیاده کند:

```text
publish(platform_context) ->
  success(external_id, external_url)
  OR
  failure(error_code, error_message, retryable)
```

Business Rule نباید داخل Adapter باشد.

مثلاً Adapter حق ندارد خودش تصمیم بگیرد Content بدون Approval منتشر شود؛ چون اصلاً Event انتشار برای محتوای تأییدنشده از Backend تولید نمی‌شود.

## Retry Policy پیشنهادی

### Retryable

- HTTP 429
- Timeout
- HTTP 502/503/504
- Temporary network error

### Non-retryable

- Invalid credential
- Permission denied
- Invalid media format
- Deleted destination
- Policy rejection

برای Retryهای واقعی در فاز Worker، Backoff به شکل تقریبی زیر پیشنهاد می‌شود:

```text
1m → 5m → 15m → 1h → Dead Letter / Human Review
```

## Observability

هر Execution باید حداقل این Context را در Log داشته باشد:

```text
workspace_id
content_id
publication_id
event_id
idempotency_key
platform
provider_result
execution_id
```

هیچ Token یا Secret نباید Log شود.

## Naming Convention

```text
RE-PUB-001 | Outbox Dispatcher
RE-PUB-010 | Telegram Adapter
RE-PUB-020 | Instagram Adapter
RE-PUB-030 | LinkedIn Adapter
RE-ERR-001 | Automation Failure Handler
```

## Definition of Done برای اولین Adapter واقعی

- Credential خارج از Workflow است.
- Provider Sandbox/Test destination استفاده شده.
- Success callback تست شده.
- Failure callback تست شده.
- 429/timeout behavior مشخص است.
- Duplicate Event باعث Duplicate Post نمی‌شود یا limitation Provider مستند شده است.
- Logها Secret ندارند.
- اجرای Workflow قابل ردیابی با `publication_id` است.
- Runbook خطا نوشته شده است.

تا قبل از این Gate، Adapter نباید برای مشتری Production فعال شود.
