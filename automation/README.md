# Automation Runtime — n8n

این پوشه محل Workflowهای قابل نسخه‌بندی محصول است.

## اصل کلیدی
n8n **منبع حقیقت سیستم نیست**. وضعیت پایدار کسب‌وکار در PostgreSQL نگهداری می‌شود و n8n فقط Orchestration، Integration و اجرای Automation را انجام می‌دهد.

## ساختار پیشنهادی

```text
automation/
├── content/
├── publishing/
├── inbox/
├── leads/
├── followups/
├── analytics/
└── shared/
```

## قرارداد هر Workflow
هر Workflow باید:

1. ورودی مشخص و مستند داشته باشد.
2. `workspace_id` و `correlation_id` را عبور دهد.
3. Idempotent باشد یا Idempotency Key دریافت کند.
4. Secret را داخل JSON ذخیره نکند.
5. Timeout، Retry و Failure Path داشته باشد.
6. در خطا Event/Log قابل رهگیری تولید کند.
7. Business Rule اصلی را داخل Workflow دفن نکند.
8. خروجی Machine-readable داشته باشد.

## Naming

`<domain>.<action>.v<major>`

نمونه:

- `content.generate.v1`
- `publishing.instagram.v1`
- `inbox.ingest.v1`
- `lead.followup.v1`

## Human Approval
انتشار عمومی، پیام حساس یا اقدام غیرقابل بازگشت باید در صورت نیاز از Approval Gate عبور کند.

## ممنوع

- نگهداری CRM در Google Sheets به عنوان Source of Truth
- Hardcode کردن API Key
- ساخت Workflowهای عظیم چندمنظوره
- اجرای عملیات بدون Tenant Context
- Auto-reply بدون Stop Condition
