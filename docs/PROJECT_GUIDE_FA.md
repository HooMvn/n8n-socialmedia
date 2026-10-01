# راهنمای جامع پروژه Risheh Engage

## 1) این پروژه چیست؟

Risheh Engage یک پلتفرم هوشمند برای **تولید محتوا، انتشار، مدیریت مکالمات مشتری، تبدیل تعامل به Lead و پیگیری فروش** است.

هدف محصول این نیست که فقط چند Workflow در n8n داشته باشیم؛ هدف، ساخت یک محصول پایدار و قابل توسعه است که n8n در پشت صحنه موتور Automation آن باشد.

هسته ارزش محصول:

```text
Content → Conversation → Lead → Follow-up → Conversion → Learning
```

## 2) مسئله‌ای که حل می‌کنیم

کسب‌وکارها معمولاً چند مشکل هم‌زمان دارند:

- تولید محتوا زمان‌بر و پراکنده است.
- انتشار محتوا بین چند کانال دستی است.
- کامنت و پیام مشتری گم می‌شود.
- Leadها وارد یک سیستم منظم نمی‌شوند.
- Follow-up وابسته به حافظه افراد است.
- ارتباط بین محتوا و فروش قابل اندازه‌گیری نیست.

Risheh Engage این بخش‌ها را در یک چرخه واحد به هم وصل می‌کند.

## 3) نقش اجزای سیستم

### Next.js
رابط کاربری محصول: داشبورد، تقویم محتوا، Inbox، CRM سبک، Approval و گزارش‌ها.

### FastAPI
هسته Business Logic. تمام Ruleهای اصلی محصول باید اینجا یا در Domain Layer باشند، نه داخل n8n.

### PostgreSQL
Source of Truth. داده دائمی مشتری، محتوا، لید، Workspace، Approval و Audit اینجا ذخیره می‌شود.

### Redis
برای Cache، Rate Limit، Lock، Queue coordination و داده‌های موقت استفاده می‌شود.

### n8n
برای Orchestration و Integration:

- اجرای Workflow
- اتصال APIها
- Publish
- Webhook processing
- Follow-up timing
- Notification

### AI Providers
برای تولید محتوا، Classification، Summarization و پیشنهاد پاسخ. خروجی AI همیشه باید تحت Ruleهای سیستم باشد.

## 4) جریان نمونه واقعی

فرض کنید یک فروشگاه می‌خواهد محصول جدید معرفی کند:

1. مدیر Brief یا URL محصول را وارد می‌کند.
2. Content Engine چند ایده و Caption تولید می‌کند.
3. مدیر محتوا را تأیید می‌کند.
4. n8n انتشار را اجرا می‌کند.
5. مشتری در Instagram کامنت می‌گذارد.
6. Webhook پیام را وارد Inbox می‌کند.
7. Intent Detection پیام را «درخواست قیمت» تشخیص می‌دهد.
8. Customer Identity ساخته/Match می‌شود.
9. Lead ساخته می‌شود.
10. Follow-up Rule فعال می‌شود.
11. در صورت نیاز Human Handoff انجام می‌شود.
12. نتیجه در Analytics ثبت می‌شود.

## 5) مرزبندی Domainها

### Identity & Workspace
کاربر، Workspace، Membership و دسترسی‌ها.

### Brand Brain
Tone of Voice، خدمات، محصول، FAQ، قوانین برند و Knowledge Sources.

### ContentOps
Idea، Draft، Variant، Calendar، Approval و Publication.

### Conversation Hub
Channel، Conversation، Message، Intent، Assignment و Human Handoff.

### Customer & LeadOps
Customer، Identity، Lead، Pipeline، Activity و Follow-up.

### Integrations
Instagram، Telegram، WhatsApp، Email، CRM یا سرویس‌های دیگر از طریق Adapter.

### Automation Runtime
اجرای n8n Workflow و ثبت AutomationRun، Retry و Failure.

### Analytics
Content Performance، Lead Conversion و attribution.

## 6) قانون طلایی معماری

### Business Rule داخل n8n دفن نمی‌شود.

بد:

```text
Webhook → 45 Node → شرط فروش → دیتای CRM → Google Sheet → ارسال
```

خوب:

```text
Webhook
  ↓
API
  ↓
Domain Rule
  ↓
Database
  ↓
Domain Event
  ↓
n8n Integration Workflow
```

## 7) Source of Truth چیست؟

هر داده باید مالک مشخص داشته باشد.

| داده | مالک |
|---|---|
| Customer | PostgreSQL |
| Lead | PostgreSQL |
| Content Status | PostgreSQL |
| Approval | PostgreSQL |
| Workflow Execution | n8n + AutomationRun metadata |
| Cache | Redis |
| فایل Media | Object Storage در فاز بعد |

## 8) Multi-tenancy

هر مشتری تجاری یک Workspace مستقل دارد. تمام رکوردهای Tenant-bound باید `workspace_id` داشته باشند و هیچ Query نباید داده Workspace دیگر را برگرداند.

این موضوع صرفاً Feature نیست؛ Security Boundary است.

## 9) Human-in-the-loop

AI نباید بدون کنترل در تمام مسیر تصمیم نهایی بگیرد. نمونه اقداماتی که ممکن است Approval بخواهند:

- Publish عمومی
- پاسخ حساس
- تخفیف یا پیشنهاد مالی
- حذف محتوا
- تغییر وضعیت مهم Lead

## 10) Idempotency

Webhook ممکن است دوبار ارسال شود. اگر سیستم برای هر بار یک Lead جدید بسازد، محصول قابل اعتماد نیست.

هر Event ورودی باید شناسه‌ای داشته باشد که Duplicate را تشخیص دهد.

نمونه:

```text
provider + external_event_id + workspace_id
```

## 11) Observability

برای هر درخواست/Workflow بهتر است این شناسه‌ها قابل رهگیری باشند:

- `request_id`
- `correlation_id`
- `workspace_id`
- `automation_run_id`

هدف: بتوانیم از UI تا API و n8n مسیر یک خطا را پیدا کنیم.

## 12) امنیت پایه

- Secret داخل Git ممنوع.
- Webhook باید Signature/Secret Validation داشته باشد.
- Permissionها Least Privilege باشند.
- AI ورودی خارجی را Trusted Instruction فرض نکند.
- PII فقط در صورت نیاز ذخیره شود.
- Log نباید Token یا Credential چاپ کند.

## 13) روش توسعه Feature جدید

قبل از کدنویسی پاسخ دهید:

1. Actor کیست؟
2. Problem چیست؟
3. Domain مالک Feature کدام است؟
4. داده دائمی چیست؟
5. External Integration چیست؟
6. Failure Path چیست؟
7. Permission چیست؟
8. Metric موفقیت چیست؟

بعد Vertical Slice بسازید:

```text
UI → API → Domain → DB → Event → Automation → Test
```

## 14) Definition of Done

Feature تمام نشده مگر اینکه:

- Happy Path تست شده باشد.
- Failure Path مشخص باشد.
- Tenant Isolation رعایت شود.
- Log/Audit مناسب وجود داشته باشد.
- Secret اضافه نشده باشد.
- Documentation در صورت تغییر معماری آپدیت شود.
- UI وضعیت Loading/Error/Empty را پوشش دهد.

## 15) اولین Vertical Slice پیشنهادی

```text
Brand Setup
   ↓
Generate Content
   ↓
Review
   ↓
Approve
   ↓
Publish
   ↓
Publication Status
```

پس از پایدار شدن:

```text
Inbound Message
   ↓
Customer Match
   ↓
Conversation
   ↓
Lead
   ↓
Follow-up
```

## 16) چیزی که فعلاً نمی‌سازیم

برای جلوگیری از Scope Creep در MVP:

- Billing پیچیده SaaS
- CRM کامل سازمانی
- Social Listening گسترده
- Attribution چندلمسی پیشرفته
- Microservices
- Recommendation Engine سنگین

ابتدا باید یک End-to-End Flow قابل فروش داشته باشیم.
