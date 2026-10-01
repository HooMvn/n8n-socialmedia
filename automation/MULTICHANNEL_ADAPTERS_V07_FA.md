# راهنمای Multi-channel Adapter — Risheh Engage v0.7

## هدف
Core نباید Instagram/WhatsApp/Telegram-specific شود. هر Provider باید داده را به Contract عمومی Risheh Engage تبدیل کند.

```text
Provider Webhook
   ↓
Verify Provider Signature / Secret
   ↓
Normalize
   ↓
Generic Inbound Contract
   ↓
FastAPI
```

## Generic Inbound Contract

```json
{
  "channel": "instagram",
  "external_user_id": "provider-user-id",
  "external_message_id": "provider-message-id",
  "username": "optional",
  "display_name": "optional",
  "phone": null,
  "email": null,
  "body": "متن پیام"
}
```

Endpoint:

```text
POST /api/v1/automation/workspaces/{workspace_id}/inbound
```

## Outbound Contract

Provider Adapter نباید Customer ID را به‌عنوان Provider ID فرض کند. قبل از ارسال:

```text
OutboundMessage
  ↓
Delivery Context
  ↓
CustomerIdentity
  ↓
external_user_id
```

## Telegram
Workflowهای v0.4 تا v0.6 موجود هستند و Publish/Inbound/Outbound را پوشش می‌دهند.

## Instagram Foundation
برای Instagram Adapter این Gateها اجباری‌اند:
- Meta app credentials برای همان Workspace
- Webhook verification
- signature verification
- mapping sender/message IDs به Generic Contract
- rate-limit handling
- delivery/error callback
- عدم نگهداری access token داخل Workflow JSON

## WhatsApp Foundation
برای WhatsApp Cloud Adapter:
- Workspace-scoped credential
- webhook verification
- phone-number/account mapping
- message ID deduplication
- opt-out/consent enforcement
- template-message policy در جای لازم
- delivery status normalization

## Secret Rule
Credential باید از `provider_credentials` یا Secret Manager خوانده شود. Token داخل GitHub/n8n workflow export ممنوع است.

## Provider Adapter Interface
هر Adapter باید حداقل این عملیات را پوشش دهد:

```text
verify_webhook()
normalize_inbound()
resolve_delivery_target()
send_message()
normalize_delivery_status()
classify_provider_error()
```

## Error Classes
- retryable: timeout, 429, transient 5xx
- non-retryable: invalid recipient, revoked permission, malformed payload
- credential: invalid/expired token → mark credential invalid + human alert

## Definition of Done برای Adapter واقعی
- live webhook verified
- inbound dedup tested
- outbound callback tested
- retry path tested
- credential rotation tested
- opt-out tested
- cross-tenant credential isolation tested
- no secret in logs/export

> v0.7 Adapter Architecture آماده است؛ Instagram/WhatsApp تا زمان Live Credential Smoke نباید Production-ready اعلام شوند.
