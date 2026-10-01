# مدل دامنه Risheh Engage

این سند مدل مفهومی اولیه محصول را تعریف می‌کند. هدف آن ساخت دیتابیس نهایی نیست؛ هدف، مشخص کردن Entityها، Ownership و رابطه‌های اصلی قبل از شروع Implementation است.

## 1. Workspace

مرز اصلی Tenant.

فیلدهای مفهومی:

- id
- name
- slug
- status
- timezone
- locale
- created_at

تمام داده‌های تجاری متعلق به Workspace هستند.

## 2. User / Membership

User هویت فرد است و Membership رابطه فرد با Workspace.

Membership:

- workspace_id
- user_id
- role
- status

یک User می‌تواند عضو چند Workspace باشد.

## 3. BrandProfile

اطلاعاتی که AI و تیم محتوا برای شناخت برند نیاز دارند.

- workspace_id
- name
- description
- tone_of_voice
- audience
- writing_rules
- forbidden_terms
- default_cta_policy

## 4. KnowledgeSource

منابع Brand Brain.

انواع احتمالی:

- text
- website
- faq
- product_catalog
- document
- approved_content

## 5. Campaign

یک هدف بازاریابی دارای بازه و هدف مشخص.

- workspace_id
- name
- objective
- start_at
- end_at
- status
- target_audience
- offer

## 6. ContentItem

واحد canonical محتوا.

- workspace_id
- campaign_id nullable
- title
- content_type
- source_type
- status
- body / structured_payload
- created_by
- scheduled_at nullable

ContentItem می‌تواند چند PlatformVariant داشته باشد.

## 7. PlatformVariant

نسخه مخصوص یک Channel.

مثلاً یک Campaign Idea دارای:

- Instagram Reel Script
- Telegram Post
- LinkedIn Post

هر Variant باید مستقل approve/publish شود.

## 8. Approval

Approval یک Entity واقعی است.

- entity_type
- entity_id
- requested_by
- reviewer_id
- state
- comment
- decided_at

State:

```text
PENDING
APPROVED
REJECTED
CHANGES_REQUESTED
```

## 9. Publication

نماینده یک تلاش انتشار.

- content_variant_id
- channel_connection_id
- scheduled_at
- published_at
- external_post_id
- status
- failure_reason

Status:

```text
QUEUED
PROCESSING
PUBLISHED
FAILED
CANCELLED
```

## 10. IntegrationConnection

اتصال یک Workspace به Provider.

- provider
- workspace_id
- account_reference
- status
- scopes
- secret_reference

Token خام بهتر است در vault/secret store باشد؛ DB فقط reference/metadata را نگه دارد.

## 11. Customer

هویت canonical مشتری.

- workspace_id
- display_name
- phone nullable
- email nullable
- status
- owner_id nullable
- last_interaction_at

## 12. CustomerIdentity

اتصال Customer به هویت یک Channel.

مثال:

```text
Customer #42
 ├─ Instagram: @user
 ├─ Telegram: 123456
 ├─ WhatsApp: +98...
 └─ Email: x@example.com
```

فیلدها:

- customer_id
- provider
- external_id
- username nullable
- verified_at nullable

Unique constraint باید از duplicate identity جلوگیری کند.

## 13. Conversation

یک Thread مکالمه در یک Channel.

- customer_id
- channel
- channel_connection_id
- external_thread_id
- status
- assigned_to
- intent
- priority
- last_message_at

## 14. Message

- conversation_id
- external_message_id
- direction: inbound/outbound
- sender_type: customer/agent/ai/system
- body
- message_type
- received_at/sent_at
- delivery_status

پیام ورودی با external ID باید idempotent ingest شود.

## 15. Lead

فرصت تجاری.

- workspace_id
- customer_id
- source_channel
- source_content_id nullable
- campaign_id nullable
- status
- score
- owner_id
- next_followup_at
- estimated_value nullable

## 16. LeadActivity

Timeline فروش.

نمونه type:

- lead_created
- contacted
- note_added
- followup_scheduled
- proposal_sent
- status_changed
- won
- lost

## 17. FollowUp

- lead_id
- type
- due_at
- assigned_to
- status
- automation_policy

Status:

```text
PENDING
DONE
CANCELLED
SKIPPED
FAILED
```

## 18. AutomationRun

هر اجرای مهم n8n یا worker قابل ردیابی است.

- workspace_id
- workflow_key
- workflow_version
- event_id
- entity_type
- entity_id
- status
- started_at
- completed_at
- attempt
- error_code

## 19. AuditLog

برای عملیات حساس.

- workspace_id
- actor_type
- actor_id
- action
- entity_type
- entity_id
- before/after metadata در حد لازم
- created_at

## 20. MetricEvent

Event خام Analytics.

مثال:

- content_published
- content_clicked
- conversation_started
- lead_created
- lead_qualified
- conversion_recorded

Analytics نباید Business State canonical را جایگزین کند.

---

# روابط اصلی

```text
Workspace
 ├─ Membership ─ User
 ├─ BrandProfile
 ├─ Campaign
 │    └─ ContentItem
 │         └─ PlatformVariant
 │              ├─ Approval
 │              └─ Publication
 │
 ├─ Customer
 │    ├─ CustomerIdentity
 │    ├─ Conversation
 │    │    └─ Message
 │    └─ Lead
 │         ├─ LeadActivity
 │         └─ FollowUp
 │
 ├─ IntegrationConnection
 └─ AutomationRun
```

# Constraintهای مهم

1. تمام Entityهای tenant-owned باید workspace scope داشته باشند.
2. external message IDs باید در محدوده Provider/Connection unique باشند.
3. Lead می‌تواند از Content/Campaign قابل attribution باشد.
4. حذف Integration نباید history تجاری را حذف کند.
5. Customer merge باید در آینده قابل پشتیبانی باشد.
6. Provider-specific payload نباید Domain schema را آلوده کند؛ raw metadata در boundary مناسب نگهداری شود.
7. Statusها با Domain transition تغییر می‌کنند، نه update آزاد از هر client.
