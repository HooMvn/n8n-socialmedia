# دانشنامه فنی Risheh Engage — v0.5

این فایل واژه‌نامه عمومی پروژه است. برای Customer Communication جزئیات بیشتر را در `CUSTOMER_COMMUNICATION_GLOSSARY_FA.md` بخوانید.

---

# 1) Architecture & Backend

### API
قرارداد ارتباط Frontend، Adapterها یا سرویس‌ها با Backend.

### Endpoint
یک مسیر مشخص API مثل `POST /api/v1/workspaces`.

### FastAPI
فریم‌ورک Python برای API تایپ‌شده، async و قابل مستندسازی.

### Domain
مرز منطقی کسب‌وکار؛ مثل Content، Customer، Conversation یا Lead.

### Business Logic
قواعد واقعی محصول؛ مثل «محتوای تأییدنشده Publish نشود» یا «Lead با score بالا Qualified شود».

### Modular Monolith
یک اپلیکیشن deployable واحد با Moduleهای Domain جدا و مرزهای واضح. انتخاب فعلی پروژه برای جلوگیری از پیچیدگی زودهنگام Microservice.

### Vertical Slice
پیاده‌سازی End-to-End یک جریان واقعی از UI/API تا Database و Integration، نه ساخت لایه‌ها به‌صورت جدا و نیمه‌کاره.

### Event-driven Architecture
بخش‌های سیستم به Eventهای مهم واکنش نشان می‌دهند به‌جای coupling مستقیم و شکننده.

### Domain Event
بیان یک اتفاق کسب‌وکاری مثل `content.publish.requested`.

### Adapter Pattern
قرار دادن Provider پشت Interface/Contract عمومی تا Core به Telegram یا Instagram قفل نشود.

### Orchestration
هماهنگی چند مرحله و سرویس. در این پروژه n8n Orchestrator است، نه مالک State.

---

# 2) Data & PostgreSQL

### PostgreSQL
Source of Truth اصلی محصول.

### Source of Truth
مرجع رسمی داده. وضعیت Lead از DB خوانده می‌شود، نه از n8n یا Sheet.

### Entity
شیء دارای هویت پایدار مثل Customer یا Lead.

### Primary Key
شناسه اصلی رکورد؛ در پروژه عموماً UUID.

### Foreign Key
قید رابطه بین دو Table و ابزار مهم Integrity.

### Unique Constraint
قانون دیتابیس برای جلوگیری از Duplicate.

### Composite Unique Constraint
Unique روی چند ستون؛ مثلاً:
`workspace_id + channel + external_message_id`.

### Index
ساختار بهینه‌سازی Query. Index باید بر اساس مسیرهای خواندن واقعی انتخاب شود.

### Transaction
چند عملیات که یا همه Commit می‌شوند یا همه Rollback.

### Migration
نسخه‌بندی Schema با Alembic.

### ORM
نگاشت Objectهای Python به Tableهای DB؛ این پروژه SQLAlchemy استفاده می‌کند.

### AsyncSession
Session غیرهمزمان SQLAlchemy برای Query/Transaction در FastAPI.

---

# 3) SaaS & Security

### Workspace / Tenant
مرز یک مشتری سازمانی در SaaS.

### Multi-tenancy
چند Workspace روی یک Product واحد با جداسازی داده.

### Tenant Isolation
جلوگیری از دسترسی Workspace A به داده Workspace B.

### Authentication
اثبات اینکه User چه کسی است.

### Authorization
تعیین اینکه User چه کاری اجازه دارد انجام دهد.

### JWT
Token امضاشده برای Authentication درخواست API.

### Argon2
الگوریتم Password Hashing مقاوم برای ذخیره امن‌تر Password.

### RBAC
Role-Based Access Control؛ Permission بر اساس Role/Membership.

### Membership
رابط User و Workspace همراه Role.

### Least Privilege
دادن حداقل Permission لازم.

### PII
اطلاعات قابل شناسایی فرد مثل Phone و Email.

### Data Minimization
ذخیره فقط اطلاعات لازم برای هدف محصول.

### Secret Management
نگهداری Token/API key خارج از Source Code و Log.

---

# 4) Reliability & Distributed Work

### Idempotency
تکرار یک درخواست نباید نتیجه Business را چند بار ایجاد کند.

### Deduplication
تشخیص و حذف Event/Message تکراری.

### Retry
تلاش مجدد بعد از خطای موقت.

### Exponential Backoff
افزایش فاصله Retryها برای جلوگیری از فشار و retry storm.

### Dead Letter
محل/State نگهداری Jobهایی که پس از Retryهای مجاز همچنان Fail شده‌اند.

### Stale Lock
Lockی که Worker به‌علت Crash رها نکرده و باید پس از timeout قابل بازیابی باشد.

### `FOR UPDATE SKIP LOCKED`
الگوی PostgreSQL برای Claim کردن امن Jobها توسط چند Worker بدون پردازش همزمان یک رکورد.

### At-least-once Delivery
Event ممکن است بیش از یک بار Deliver شود اما نباید گم شود؛ Consumer باید Idempotent باشد.

### Exactly-once
در سیستم‌های توزیع‌شده معمولاً ادعای سختی است؛ باید با Idempotency/ledger/reconciliation طراحی شود، نه فرض شود.

### Transactional Outbox
ثبت Event در همان Transaction تغییر Business State، سپس تحویل async توسط Worker.

---

# 5) n8n & Automation

### Workflow
فرآیند Automation از Nodeها.

### Node
مرحله Workflow مثل Webhook، HTTP Request یا Code.

### Trigger
شروع Workflow با Schedule/Webhook/Event.

### Webhook
Endpoint دریافت Event خارجی.

### Webhook Replay
ارسال دوباره همان Event توسط Provider؛ رفتار طبیعی است و باید Idempotent مدیریت شود.

### Credential
Secret یا احراز هویت Provider.

### Channel Adapter
لایه‌ای که Telegram/Instagram/WhatsApp payload را به Contract عمومی Core تبدیل می‌کند.

### Provider Adapter
لایه‌ای که درخواست عمومی Core را به API اختصاصی Provider تبدیل می‌کند.

### Workflow Spaghetti
پخش Business Logic در IFها و Nodeهای زیاد و غیرقابل تست؛ ضدالگوی اصلی این پروژه.

---

# 6) Customer Communication

### Customer
هویت Business-level فرد در Workspace.

### CustomerIdentity
هویت آن Customer در یک Channel خاص مثل Telegram user ID.

### Identity Resolution
تشخیص اینکه یک Identity به کدام Customer تعلق دارد.

### Customer 360
Timeline یکپارچه Identityها، Conversationها، Leadها، Follow-upها و بعداً Order/Revenue.

### Unified Inbox
نمای واحد Conversationهای چند Channel روی Domain مشترک.

### Conversation
Thread مکالمه؛ Container چند Message.

### Message
واحد پیام مستقل با Direction، Author و external ID.

### Inbound
Customer → Business.

### Outbound
Business/AI/Human → Customer.

### Message Direction
جهت پیام: inbound یا outbound.

### Author Type
نویسنده منطقی Message: customer، ai، human، system.

### Intent
هدف پیام مثل pricing، support، complaint.

### Intent Classification
تبدیل متن به Intent ساختاریافته.

### Confidence
درجه اطمینان Classifier از 0 تا 100.

### Sentiment
حس/لحن پیام؛ با Intent متفاوت است.

### Human Handoff
انتقال Conversation به اپراتور انسانی.

### Assignment
اختصاص Conversation/Lead/Follow-up به User مشخص.

### Routing Policy
قواعد تعیین مسیر `ai_draft` یا `human_required` بر اساس Risk و Confidence.

---

# 7) CRM & LeadOps

### Lead
Customer با سیگنال فروش که باید در Pipeline پیگیری شود.

### Lead Qualification
ارزیابی جدیت/تناسب Lead.

### Lead Score
امتیاز اولویت Lead.

### Pipeline
مراحل فروش:
`new → qualified → contacted → proposal → won/lost`.

### Follow-up
اقدام زمان‌دار برای پیگیری Lead؛ الزاماً Message خودکار نیست.

### Stop Condition
شرط توقف Automation مثل reply، won/lost، opt-out یا human stop.

### Attribution
نسبت دادن Conversation/Lead/Revenue به Channel، Content یا Campaign.

---

# 8) AI Engineering

### LLM
Large Language Model.

### Prompt
دستور/Context ورودی مدل.

### System Prompt
قواعد سطح بالای Agent.

### Structured Output
خروجی مطابق Schema مثل JSON برای پردازش امن‌تر.

### RAG
Retrieval-Augmented Generation؛ بازیابی Knowledge قبل از Generation.

### Embedding
بردار عددی برای Semantic Search.

### Hallucination
تولید اطلاعات نادرست با ظاهر معتبر.

### Prompt Injection
تلاش ورودی برای تغییر دستورهای Agent.

### Guardrail
کنترل Policy/Validation برای محدود کردن رفتار AI.

### Human-in-the-loop
حضور انسان در نقاط حساس تصمیم یا Approval.

### AI Draft
پیشنهاد AI که هنوز Action نهایی نیست.

### Evaluation
اندازه‌گیری کیفیت AI با Dataset و Metric، نه فقط مشاهده دستی چند پاسخ.

---

# 9) Frontend / UX

### Next.js
Framework اصلی Web.

### React
کتابخانه Component-based UI.

### Client Component
Component نیازمند browser state/event.

### Server Component
Component قابل اجرا در Server در App Router.

### Loading State
تجربه انتظار داده.

### Empty State
تجربه بدون داده.

### Error State
تجربه قابل فهم Failure.

### Conversation UX
طراحی Thread، assignment، status، handoff و response actions به شکل سریع و کم‌خطا.

---

# 10) Testing / DevOps / Observability

### Unit Test
تست یک Function/Policy کوچک.

### Contract Test
تست ثابت بودن Schema/Enum/Interface بین اجزا.

### Integration Test
تست تعامل API + PostgreSQL یا Worker + DB.

### E2E
تست مسیر واقعی کاربر و Integrationها.

### Smoke Test
بررسی سریع مسیر حیاتی بعد از Deploy.

### CI
Build/Test خودکار روی Commit/PR.

### Docker
Container packaging.

### Docker Compose
اجرای مجموعه API/Web/DB/Redis/n8n/Worker.

### Observability
توان فهم وضعیت سیستم با Log، Metric و Trace.

### Structured Log
Log با Fieldهای ماشینی مانند workspace_id و correlation_id.

### Correlation ID
شناسه دنبال‌کردن یک جریان بین API، Worker و n8n.

### Audit Log
رکورد اینکه چه User/Service چه تغییر حساس Business/Security انجام داده است.

---

# مفاهیم اجباری قبل از توسعه

توسعه‌دهنده باید بتواند بدون حفظ‌کردن متن، این تفاوت‌ها را توضیح دهد:

- Authentication vs Authorization
- Customer vs CustomerIdentity
- Conversation vs Message
- Intent vs Sentiment
- Lead vs Customer
- Follow-up vs Message
- Retry vs Idempotency
- n8n State vs Product State
- Channel Adapter vs Business Domain
- AI Draft vs Business Action
- Source of Truth vs Cache
- Tenant ID vs Tenant Authorization
