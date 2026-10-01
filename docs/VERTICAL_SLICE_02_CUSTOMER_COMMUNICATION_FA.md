# Vertical Slice 02 — Customer Communication

نسخه: `v0.5`

این سند مرجع فنی و آموزشی مسیر **پیام ورودی تا لید و پیگیری** در Risheh Engage است.

## هدف

ساخت یک جریان واقعی و قابل‌اندازه‌گیری:

```text
Inbound Message
→ Customer Identity
→ Customer
→ Conversation
→ Message
→ Intent
→ AI / Human Handoff
→ Lead
→ Follow-up
```

## چرا این Slice مهم است؟

ContentOps بدون ConversationOps فقط تولید و انتشار محتواست. ارزش تجاری محصول زمانی شکل می‌گیرد که تعامل مخاطب به Customer، Lead و Follow-up قابل پیگیری تبدیل شود.

## مدل داده

### Customer
هویت تجاری واحد فرد در Workspace. یک Customer می‌تواند چند Identity کانالی داشته باشد.

### CustomerIdentity
نگاشت هویت خارجی به Customer داخلی:

```text
Telegram user id ─┐
Instagram user id ├→ Customer
Website visitor ──┘
```

کلید یکتا:
`workspace_id + channel + external_user_id`

### Conversation
یک Thread مکالمه در یک Channel. وضعیت‌ها:
- `open`
- `waiting_human`
- `resolved`
- `closed`

### Message
هر پیام یک رکورد مستقل است. کلید dedup:
`workspace_id + channel + external_message_id`

### Lead
نمای فروش از Customer. Pipeline فعلی:
`new → qualified → contacted → proposal → won/lost`

### FollowUp
تعهد عملی برای پیگیری Lead در زمان مشخص.

## Inbound Contract

Endpoint داخلی Adapterها:

`POST /api/v1/automation/workspaces/{workspace_id}/inbound`

Header:
`X-Automation-Secret`

Payload نمونه:

```json
{
  "channel": "telegram",
  "external_user_id": "12345",
  "external_message_id": "98765",
  "username": "customer_name",
  "display_name": "مشتری نمونه",
  "body": "قیمت سرویس طراحی سایت چقدره؟"
}
```

## Idempotency ورودی

Webhookها ممکن است چندبار Deliver شوند. اگر `external_message_id` قبلاً ثبت شده باشد، API همان Customer/Conversation/Message قبلی را برمی‌گرداند و `duplicate=true` می‌شود.

## Customer Resolution

ترتیب فعلی:
1. Channel + External User ID را پیدا کن.
2. اگر Identity موجود است، Customer را reuse کن.
3. اگر نیست، Customer و Identity جدید بساز.
4. اطلاعات جدید مثل phone/email فقط در صورت خالی بودن enrich می‌شوند.

در نسخه‌های بعد Identity Resolution می‌تواند phone/email verified و merge policy داشته باشد.

## Conversation Reuse

برای همان Customer و Channel، آخرین Conversation با وضعیت `open` یا `waiting_human` reuse می‌شود. Conversation بسته‌شده دوباره باز نمی‌شود؛ پیام بعدی Thread جدید می‌سازد.

## Intent

Endpoint:
`POST /workspaces/{workspace_id}/conversations/{conversation_id}/intent`

Intent نمونه:
- `pricing`
- `sales_interest`
- `support`
- `complaint`
- `appointment`
- `general_question`
- `spam`

Confidence بین 0 تا 100 ذخیره می‌شود.

اصل مهم: **LLM فقط Intent پیشنهاد می‌دهد؛ Domain State توسط API تغییر می‌کند.**

## Human Handoff

وقتی پیام حساس است یا Confidence پایین است:

```text
AI / Rule Engine
↓
Handoff
↓
waiting_human
↓
assigned_user_id
```

پیشنهاد Policy:
- complaint → Human
- refund/financial commitment → Human
- confidence < 75 → Human
- pricing عمومی با KB معتبر → AI draft مجاز

## Lead Creation

Conversation می‌تواند به Lead تبدیل شود. Lead برای هر Customer در Workspace یکتا است تا duplicate pipeline نسازیم.

Lead Score فعلی 0..100 است. اگر Score >= 70 و Lead هنوز `new` باشد، به `qualified` می‌رود.

این Rule ساده است و بعداً باید با Rule Engine / scoring model جایگزین شود.

## Follow-up

هر FollowUp باید:
- `due_at`
- `reason`
- `assigned_user_id` اختیاری
- `status`

داشته باشد.

Automation آینده باید در صورت Reply، Won/Lost، Opt-out یا Human Stop، sequence مناسب را متوقف کند.

## RBAC

- Viewer/Analyst: مشاهده Inbox و Customer/Lead
- Editor: طبقه‌بندی Intent و کار محتوایی
- Reviewer/Admin/Owner: Handoff، Lead management، Follow-up

## Multi-tenancy

تمام Queryهای Business باید با `workspace_id` Scope شوند. UUID به‌تنهایی مجوز نیست.

## مواردی که عمداً هنوز انجام نشده

- AI auto-reply واقعی
- Knowledge Base / RAG برای پاسخ
- Outbound Message Adapter عمومی
- Telegram inbound workflow آماده import
- Instagram/WhatsApp adapters
- SLA timer و escalation
- Customer merge UI
- full Customer 360 timeline
- lead attribution to content/campaign

این موارد باید به شکل مرحله‌ای و تست‌پذیر اضافه شوند، نه در یک Workflow بزرگ.

## Definition of Done برای Slice 02

- inbound duplicate دوباره Message نسازد
- Channel identity به Customer پایدار وصل شود
- Conversation history قابل خواندن باشد
- Intent قابل ثبت باشد
- Human handoff state داشته باشد
- Conversation به Lead تبدیل شود
- Lead Pipeline قابل تغییر باشد
- Follow-up قابل زمان‌بندی باشد
- تمام read/writeها tenant-scoped باشند
- API schema و migration هم‌نسخه باشند

## تمرین آموزشی تیم

1. یک پیام Telegram فرضی ingest کنید.
2. همان پیام را دوباره ارسال و `duplicate=true` را بررسی کنید.
3. پیام دوم با message id جدید ولی user id یکسان بفرستید.
4. بررسی کنید Customer جدید ساخته نشود.
5. Intent را `sales_interest` با confidence=90 ثبت کنید.
6. Lead score=80 بسازید و Qualified شدن را بررسی کنید.
7. Follow-up فردا ایجاد کنید.
8. Handoff را فعال کنید و Conversation را در `waiting_human` ببینید.
