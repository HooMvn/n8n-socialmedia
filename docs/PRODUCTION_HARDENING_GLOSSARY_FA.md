# دانشنامه تخصصی v0.7 — Grounded AI, Identity, Consent, SLA, Multi-channel

## Grounded AI
پاسخ AI که بر Context بازیابی‌شده از منابع معتبر Workspace متکی است، نه صرفاً دانش مدل.

## Knowledge Source
منبع رسمی دانش مثل FAQ، Policy، Product Guide یا Document.

## Chunking
تقسیم یک سند بزرگ به بخش‌های کوچک‌تر برای Retrieval.

## Chunk Overlap
هم‌پوشانی بین Chunkها برای کاهش از دست رفتن Context در مرزها.

## Retrieval
پیدا کردن بخش‌های مرتبط Knowledge Base برای یک Query.

## Lexical Retrieval
بازیابی بر اساس تطابق واژه‌ها. v0.7 Foundation فعلی از این روش استفاده می‌کند.

## Semantic Retrieval
جستجو بر اساس معنی، معمولاً با Embedding و Vector Search. Gate بعدی برای Scale دانش.

## Retrieval Evidence
رکورد اینکه کدام KnowledgeChunk با چه Rank/Score برای ساخت یک Draft استفاده شده است.

## RAG
Retrieval-Augmented Generation؛ ابتدا Retrieval، سپس Generation با Context بازیابی‌شده.

## Fail Closed
اگر Evidence یا Provider معتبر نداریم، عملیات حساس انجام نمی‌شود.

## Identity Verification
تأیید اینکه یک Provider Identity واقعاً متعلق به Customer موردنظر است.

## Verified Identity Merge
ادغام Identityهای چند کانال فقط بعد از Verification؛ نه بر اساس شباهت نام یا حدس AI.

## Identity Conflict
حالتی که دو Identity یا Customer claim ناسازگار دارند و Merge باید متوقف شود.

## Consent
مجوز ثبت‌شده Customer برای Purpose و Channel مشخص.

## Purpose Limitation
رضایت برای یک هدف به معنی رضایت برای همه اهداف نیست. مثلاً Support consent با Marketing consent متفاوت است.

## Opt-out
درخواست Customer برای توقف نوعی ارتباط؛ باید در Automation enforce شود.

## Suppression
قانونی که مانع ارسال پیام به Customer/Channel/Purpose خاص می‌شود.

## SLA
Service Level Agreement؛ زمان هدف برای پاسخ یا حل Conversation.

## First Response SLA
حداکثر زمان هدف تا اولین پاسخ معتبر.

## Resolution SLA
زمان هدف تا حل مسئله یا بستن Conversation.

## SLA Breach
عبور از Deadline بدون رسیدن به State مورد انتظار.

## Escalation
بالا بردن سطح رسیدگی هنگام Breach یا Risk بالا.

## Provider Credential
Secret/Token موردنیاز برای ارتباط با Provider مثل Telegram/Meta.

## Workspace-scoped Credential
Credential متعلق به یک Workspace مشخص است و Workspace دیگر نباید به آن دسترسی داشته باشد.

## Encryption at Rest
Secret در Storage به شکل Plaintext ذخیره نمی‌شود. v0.7 از Fernet با کلید مشتق‌شده از App Secret برای Foundation استفاده می‌کند؛ Production بهتر است KMS/Secret Manager داشته باشد.

## Credential Rotation
تعویض Token/Secret بدون Downtime و بدون Commit کردن Secret در GitHub.

## Channel Adapter
لایه تبدیل Provider-specific payload به Contract عمومی Core.

## Provider Adapter
بخشی که API Provider را صدا می‌زند و Error/Status آن را Normalize می‌کند.

## Delivery Context
اطلاعات لازم برای ارسال، شامل Channel، External User ID و Payload؛ از CustomerIdentity Resolve می‌شود.

## Attribution Touchpoint
یک نقطه تماس قابل اندازه‌گیری در Customer Journey.

## First-touch Attribution
اعتبار Conversion به اولین Touchpoint.

## Last-touch Attribution
اعتبار Conversion به آخرین Touchpoint پیش از Conversion.

## Multi-touch Attribution
تقسیم اعتبار بین چند Touchpoint.

## Revenue Attribution
وصل کردن Touchpoint/Content/Campaign به مبلغ Revenue؛ هنوز Production Gate بعدی است.

## Read Model
نمای تجمیعی برای خواندن سریع؛ مثل Customer 360. Read Model مالک Source of Truth نیست.

## PII
اطلاعات هویتی مثل تلفن، ایمیل و شناسه‌های قابل نسبت دادن به شخص.

## Data Retention
مدت نگهداری داده قبل از حذف/Archive طبق Policy.

## Redaction
حذف یا ماسک کردن PII از Log/Prompt/Export.

## Secret Zero
اولین Secretی که برای دسترسی به بقیه Secretها نیاز است؛ باید خارج از Repo نگهداری شود.

## تمرین اجباری تیم
تفاوت این جفت‌ها را توضیح دهید:
- Retrieval vs Generation
- Evidence vs Citation
- Customer vs Identity
- Verification vs Merge
- Consent vs Authentication
- SLA vs Retry
- Channel vs Provider
- Encryption vs Hashing
- Touchpoint vs Conversion
- Read Model vs Source of Truth
