# معماری فنی Risheh Engage

> نسخه: 0.1 — Architecture First

این سند مرجع تصمیم‌های معماری محصول است. هدف، جلوگیری از تبدیل پروژه به مجموعه‌ای از Workflowهای به‌هم‌پیوسته و غیرقابل نگهداری است.

## 1. سبک معماری

برای MVP از **Modular Monolith + Event-driven Automation** استفاده می‌کنیم.

دلیل انتخاب:

- توسعه سریع‌تر از Microservices
- Transaction و Debug ساده‌تر
- مرزبندی Domainها بدون هزینه عملیاتی بالا
- امکان استخراج سرویس‌ها در آینده
- سازگار با تیم کوچک و رشد تدریجی محصول

Microservice قبل از اثبات نیاز، ممنوع است.

## 2. لایه‌ها

### Presentation

- Next.js dashboard
- Admin UI
- Unified Inbox

### Application

FastAPI مسئول Use Caseها و orchestration درون محصول است.

نمونه:

- create_content
- approve_content
- publish_content
- create_customer_from_message
- qualify_lead
- schedule_followup

### Domain

قوانین تجاری بدون وابستگی به HTTP، n8n یا Provider خارجی.

### Infrastructure

- PostgreSQL
- Redis
- n8n
- Object Storage
- External APIs

## 3. مرز Domainها

### Identity
User، Workspace، Membership، Role

### Brand
BrandProfile، KnowledgeSource، VoicePolicy

### Content
ContentItem، Campaign، Approval، Publication

### Customer
Customer، CustomerIdentity، CustomerTimeline

### Conversation
Conversation، Message، Assignment

### Sales
Lead، PipelineStage، FollowUp، Activity

### Automation
AutomationRun، IntegrationConnection، DeliveryAttempt

### Analytics
MetricEvent، AttributionLink، AggregateSnapshot

## 4. Source of Truth

PostgreSQL منبع حقیقت است.

n8n فقط Automation Runtime است.

### ممنوع

- ذخیره وضعیت اصلی Lead در Static Data n8n
- نگهداری Customer Profile صرفاً داخل workflow
- استفاده از Google Sheets به‌عنوان دیتابیس اصلی محصول
- وابستگی business rule به نام Node یا workflow ID

## 5. Event Model

Application بعد از تغییرات مهم Domain Event ایجاد می‌کند.

نمونه Eventها:

- content.created
- content.approved
- content.publish_requested
- content.published
- message.received
- customer.created
- lead.created
- lead.qualified
- followup.due
- automation.failed

حداقل envelope:

```json
{
  "event_id": "uuid",
  "event_type": "lead.created",
  "workspace_id": "uuid",
  "occurred_at": "ISO-8601",
  "entity_id": "uuid",
  "schema_version": 1,
  "payload": {}
}
```

Eventها باید versionable باشند.

## 6. Outbox Pattern

برای eventهای مهم، ابتدا mutation و Outbox record در یک transaction ذخیره می‌شوند. Worker بعداً event را به n8n یا queue تحویل می‌دهد.

این روش جلوی وضعیت زیر را می‌گیرد:

1. Lead در DB ساخته شده.
2. ارسال webhook شکست خورده.
3. هیچ follow-upی اجرا نمی‌شود.

## 7. Idempotency

تمام ورودی‌های خارجی باید قابل Deduplicate باشند.

کلیدهای پیشنهادی:

- provider + external_message_id
- provider + external_comment_id
- publication_id + target_channel
- event_id

هر endpoint مهم automation باید `Idempotency-Key` بپذیرد یا کلید معادل Domain داشته باشد.

## 8. Integration Adapter Pattern

Core با Interface کار می‌کند:

```text
SocialPublisher
MessageProvider
AIProvider
CRMProvider
NotificationProvider
StorageProvider
```

و Implementationها قابل تعویض هستند.

نمونه:

```text
SocialPublisher
 ├─ TelegramPublisher
 ├─ InstagramPublisher
 └─ LinkedInPublisher
```

## 9. n8n Boundary

### n8n انجام می‌دهد

- API orchestration
- polling/scheduling
- external notifications
- AI pipelines
- publish jobs
- approval notification
- retryable integration tasks

### FastAPI انجام می‌دهد

- validation
- authorization
- domain transitions
- persistence
- tenancy
- audit
- canonical API contracts

### قانون

n8n هیچ‌وقت مستقیماً تصمیم امنیتی یا دسترسی کاربر نمی‌گیرد.

## 10. AI Architecture

AI از طریق Adapter Layer فراخوانی می‌شود.

```text
Application
   ↓
AI Service
   ↓
Provider Router
 ├─ OpenAI-compatible
 ├─ Anthropic-compatible
 └─ Local/Other Provider
```

Promptها باید versioned باشند.

هر AI Run بهتر است این metadata را ذخیره کند:

- prompt_version
- model
- provider
- latency
- token/cost metadata در صورت وجود
- input reference
- output reference
- approval status

## 11. Human-in-the-loop

Actionهای حساس نیازمند Policy هستند.

نمونه:

- انتشار محتوا: approval configurable
- پاسخ عمومی FAQ: auto allowed
- شکایت: human review
- refund/تعهد مالی: human required
- تغییر وضعیت مالی: AI forbidden

## 12. Multi-tenancy

MVP از Shared Database / Shared Schema استفاده می‌کند.

تمام جدول‌های tenant-owned باید `workspace_id` داشته باشند.

هیچ query بدون tenant scope پذیرفته نیست.

در آینده در صورت نیاز می‌توان tenantهای Enterprise را جدا کرد؛ اما این تصمیم برای MVP ضروری نیست.

## 13. Auth & RBAC

Roleهای اولیه:

- Owner
- Admin
- Content Manager
- Support Agent
- Sales Agent
- Analyst
- Viewer

Permission باید capability-based باشد، نه فقط role string.

نمونه:

- content.create
- content.approve
- content.publish
- inbox.reply
- lead.assign
- analytics.view
- integrations.manage

## 14. Observability

هر Request و Automation باید correlation داشته باشد.

حداقل فیلدهای log:

- timestamp
- level
- request_id
- workspace_id
- actor_id
- event_id
- automation_run_id
- integration
- error_code

PII و Secret در log ممنوع است.

## 15. Failure Strategy

External APIها قابل اعتماد فرض نمی‌شوند.

برای هر Integration:

- timeout
- bounded retry
- exponential backoff
- dead-letter / failed state
- manual replay
- circuit breaking در صورت نیاز

تعریف شود.

## 16. Data Consistency

Strong consistency برای:

- permissions
- lead state transitions
- approval state
- tenant ownership

Eventual consistency برای:

- analytics
- external publishing status
- AI enrichment
- non-critical notifications

## 17. API Design

- REST-first برای MVP
- `/api/v1`
- UUID identifiers
- ISO-8601 timestamps
- typed error codes
- pagination استاندارد
- explicit status transitions

نمونه بد:

```http
PATCH /leads/123
{"status":"won"}
```

برای transitionهای مهم ترجیحاً:

```http
POST /leads/123/actions/mark-won
```

تا rule، audit و validation واضح بمانند.

## 18. Suggested Deployment

MVP:

```text
Reverse Proxy
 ├─ Next.js
 ├─ FastAPI
 ├─ n8n
 └─ Webhooks

Private Network
 ├─ PostgreSQL
 └─ Redis
```

DB و Redis مستقیم Public نمی‌شوند.

## 19. Architecture Fitness Rules

هر PR باید این سؤال‌ها را پاس کند:

1. آیا Domain Logic وارد n8n شده؟
2. آیا integration مستقیم به Core چسبیده؟
3. آیا tenant scope وجود دارد؟
4. آیا webhook idempotent است؟
5. آیا failure قابل replay است؟
6. آیا feature قابل audit است؟
7. آیا AI خروجی را بدون policy اجرا می‌کند؟
8. آیا schema/API contract مستند است؟

اگر پاسخ نامناسب باشد، feature هنوز production-ready نیست.
