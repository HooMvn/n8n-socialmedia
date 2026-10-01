# راهنمای Telegram Inbound Adapter — Risheh Engage v0.5

این Runbook برای اتصال پیام‌های ورودی Telegram به Customer Communication Domain است.

## معماری

```text
Telegram Update
   ↓
n8n Webhook
   ↓
Normalize Telegram Payload
   ↓
Risheh Engage Inbound API
   ↓
Customer Identity Resolution
   ↓
Customer + Conversation + Message
   ↓
Unified Inbox
```

## فایل Workflow

`automation/workflows/telegram_inbound_v1.json`

نام Workflow:
`ENGAGE__INBOUND__TELEGRAM__V1`

## Environment لازم در n8n

- `RISHEH_API_BASE_URL`
- `RISHEH_AUTOMATION_SECRET`
- `RISHEH_WORKSPACE_ID`

Secret باید با `N8N_WEBHOOK_SECRET` در FastAPI یکسان باشد.

## Import

1. n8n را باز کنید.
2. Import from File را بزنید.
3. `telegram_inbound_v1.json` را انتخاب کنید.
4. Environmentها را بررسی کنید.
5. Workflow را Activate کنید.
6. Production webhook URL را بردارید.

## اتصال Telegram Bot webhook

Telegram Bot باید Updateها را به Production webhook n8n بفرستد. برای محیط Production حتماً HTTPS معتبر استفاده شود.

## Payload Normalization

Telegram payload اختصاصی در n8n به Contract عمومی تبدیل می‌شود:

```json
{
  "channel": "telegram",
  "external_user_id": "123",
  "external_message_id": "456",
  "username": "user",
  "display_name": "Example User",
  "body": "سلام، قیمت چقدره؟"
}
```

Core Backend هیچ وابستگی مستقیمی به Telegram Update schema ندارد.

## تست Deduplication

همان Update را دو بار ارسال کنید. انتظار:

- بار اول `duplicate=false`
- بار دوم `duplicate=true`
- فقط یک Message در DB

## تست Identity Reuse

دو Message با `external_message_id` متفاوت ولی `external_user_id` یکسان بفرستید. انتظار:

- یک Customer
- یک CustomerIdentity
- Conversation باز reuse شود
- دو Message مجزا

## خطاهای رایج

### 401 Invalid automation secret
`RISHEH_AUTOMATION_SECRET` و `N8N_WEBHOOK_SECRET` برابر نیستند.

### Foreign key / Workspace error
`RISHEH_WORKSPACE_ID` اشتباه است یا Workspace حذف شده است.

### unsupported telegram update
Workflow v1 فعلاً Message/Edited Message متنی یا Caption را normalize می‌کند. Callback query، media metadata و reactions فاز بعد هستند.

## Production Hardening

قبل از استفاده واقعی:

- webhook secret/verification در edge
- HTTPS
- Rate limiting
- Update type allowlist
- PII logging policy
- media download policy
- Telegram file size guard
- observability + correlation id
- dead-letter برای Adapter failure

## قانون معماری

> Telegram Adapter فقط Translator است. Customer/Conversation/Lead state باید در FastAPI + PostgreSQL بماند.
