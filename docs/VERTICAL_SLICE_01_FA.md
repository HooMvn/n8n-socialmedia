# Vertical Slice 01 — Brand → Content → Approval → Publish

این سند مسیر اولین جریان واقعی محصول Risheh Engage را تعریف می‌کند.

## هدف
کاربر در یک Workspace، پروفایل برند را می‌سازد، محتوای Draft ایجاد می‌کند، آن را برای تأیید می‌فرستد، تأیید می‌کند و درخواست انتشار را ثبت می‌کند. Backend یک رویداد قابل‌اعتماد ایجاد می‌کند و n8n فقط مسئول اجرای اتصال خارجی است. نتیجه انتشار دوباره به Backend برمی‌گردد و در PostgreSQL ثبت می‌شود.

## جریان

```text
Workspace
  ↓
Brand Profile
  ↓
Content Draft
  ↓
Submit for Review
  ↓
Approval
  ↓
Publish Request
  ↓
Outbox Event
  ↓
n8n
  ↓
Social Provider
  ↓
Publication Callback
  ↓
Publication Status
```

## قوانین مهم

1. هر رکورد business دارای `workspace_id` است.
2. Draft بدون Brand معتبر ساخته نمی‌شود.
3. فقط Content با وضعیت `approved` می‌تواند Publish شود.
4. درخواست Publish باید idempotent باشد.
5. n8n حق تغییر مستقیم Business State را ندارد؛ نتیجه را از API رسمی callback می‌کند.
6. Provider failure باید به وضعیت `failed` و خطای قابل مشاهده تبدیل شود.
7. Approval و Publication در Audit Trail قابل ردیابی‌اند.
8. AI در این Slice فقط Draft پیشنهاد می‌دهد و بدون Approval اجازه Publish ندارد.

## State Machine محتوا

```text
draft → in_review → approved → publish_requested → published
                  ↘ rejected
publish_requested → failed
failed → publish_requested
```

## Acceptance Criteria

- Workspace ساخته شود.
- Brand Profile برای Workspace ثبت و ویرایش شود.
- Content Draft ساخته و خوانده شود.
- انتقال وضعیت نامعتبر با `409 Conflict` رد شود.
- Content برای review ارسال شود.
- Approval یا Rejection ثبت شود.
- Publish فقط بعد از Approval مجاز باشد.
- Publish Request یک `OutboxEvent` بسازد.
- callback انتشار وضعیت را `published` یا `failed` کند.
- callback تکراری نتیجه دوگانه نسازد.
- تست‌ها Tenant Isolation و State Transition را پوشش دهند.

## API Contract خلاصه

```text
POST /api/v1/workspaces
POST /api/v1/workspaces/{workspace_id}/brands
GET  /api/v1/workspaces/{workspace_id}/brands

POST /api/v1/workspaces/{workspace_id}/contents
GET  /api/v1/workspaces/{workspace_id}/contents/{content_id}
POST /api/v1/workspaces/{workspace_id}/contents/{content_id}/submit-review
POST /api/v1/workspaces/{workspace_id}/contents/{content_id}/approve
POST /api/v1/workspaces/{workspace_id}/contents/{content_id}/reject
POST /api/v1/workspaces/{workspace_id}/contents/{content_id}/publish

POST /api/v1/publications/callback
GET  /api/v1/workspaces/{workspace_id}/publications/{publication_id}
```

## مسئولیت n8n

n8n Event `content.publish.requested` را دریافت می‌کند، Adapter مقصد را اجرا می‌کند و نتیجه را به callback برمی‌گرداند.

Payload ورودی نمونه:

```json
{
  "event_id": "uuid",
  "event_type": "content.publish.requested",
  "workspace_id": "uuid",
  "publication_id": "uuid",
  "content_id": "uuid",
  "platform": "telegram",
  "text": "...",
  "idempotency_key": "publish:..."
}
```

Callback نمونه:

```json
{
  "publication_id": "uuid",
  "idempotency_key": "publish:...",
  "status": "published",
  "external_id": "provider-message-id",
  "external_url": null,
  "error_code": null,
  "error_message": null
}
```

## بعد از این Slice

Slice دوم روی همین قراردادها ساخته می‌شود:

```text
Unified Inbox → Customer Identity → Conversation → Lead → Follow-up → Human Handoff
```
