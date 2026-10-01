# دانشنامه تخصصی AI + Outbound + Attribution — Risheh Engage v0.6

این فایل مکمل `TECHNICAL_GLOSSARY_FA.md` و `CUSTOMER_COMMUNICATION_GLOSSARY_FA.md` است.

---

## AI / LLM

### Intent Classifier
مدلی که هدف پیام مشتری را به یک Label ساختاریافته تبدیل می‌کند؛ مثل `price_request` یا `refund`.

### Structured Output
خروجی با Schema مشخص، معمولاً JSON. برای اتصال AI به Business Logic ضروری است.

### Confidence
عدد تخمینی اطمینان Classifier. Confidence بالا به معنی مجاز بودن Action نیست.

### Deterministic Policy
قانونی که با Code ثابت اجرا می‌شود و رفتار آن وابسته به پاسخ تصادفی LLM نیست.

### Guardrail
کنترلی برای محدود کردن یا متوقف کردن رفتار AI؛ می‌تواند Validation، Policy، Approval یا Constraint باشد.

### Fail-Closed
اگر سیستم AI مطمئن یا سالم نیست، Action انجام نمی‌شود. نقطه مقابل Fail-Open است.

### AI Draft
پیشنهاد متنی AI که هنوز برای Customer ارسال نشده است.

### Review Queue
صف Draftهایی که نیاز به بررسی، ویرایش، تأیید یا رد انسانی دارند.

### Model Provider
سرویس ارائه‌دهنده مدل AI. Core محصول نباید به Provider خاص قفل شود.

### Provider Adapter
لایه‌ای که Contract داخلی را به API یک Provider تبدیل می‌کند.

### Model Evaluation
اندازه‌گیری کیفیت مدل روی Dataset مشخص، نه فقط تست دستی چند Prompt.

### False Auto-route
موردی که پیام حساس اشتباهاً به مسیر AI خودکار منتقل شود. یکی از مهم‌ترین Risk Metricهاست.

---

## Messaging / Delivery

### Outbound Message
رکورد رسمی پیامی که سیستم قصد ارسال آن به Customer را دارد.

### Queued
پیام ساخته شده اما هنوز Provider آن را ارسال نکرده است.

### Sent
Provider ارسال اولیه را پذیرفته یا Message ID داده است.

### Delivered
تحویل به مقصد تأیید شده است؛ همه Providerها این سطح Receipt را ارائه نمی‌کنند.

### Delivery Receipt
رویدادی از Provider که وضعیت ارسال/تحویل/خوانده‌شدن را گزارش می‌کند.

### Delivery Context
اطلاعات لازم برای ارسال پیام مثل Channel، Target Identity، Body و Idempotency Key.

### Channel Adapter
لایه تبدیل Contract داخلی به API کانال، مثل Telegram یا WhatsApp.

### Target External User ID
شناسه مخاطب در Provider خارجی؛ مثلاً Telegram Chat ID. این شناسه با Customer ID داخلی فرق دارد.

### Idempotency Key
کلیدی که تکرار Request را به همان عملیات قبلی نگاشت می‌کند و از ایجاد رکورد تکراری جلوگیری می‌کند.

### At-least-once Delivery
معماری‌ای که ممکن است Event بیش از یک‌بار تحویل داده شود اما نباید گم شود. Consumer باید Idempotent باشد.

### Exactly-once
تضمین اینکه Effect دقیقاً یک بار رخ دهد. در APIهای خارجی معمولاً سخت یا غیرممکن است و باید با Dedup/Reconciliation تقریب زده شود.

### Delivery Callback
درخواست برگشتی n8n/Provider به Backend برای ثبت وضعیت واقعی Outbound.

### Provider Operation Ledger
دفتر ثبت عملیات Provider برای تشخیص Retry، Duplicate و Reconciliation. هنوز Production Gate است.

---

## Customer 360

### Customer 360
نمای یکپارچه یک Customer شامل Identityها، Conversationها، Leadها، Follow-upها و Attribution Touchpointها.

### Read Model
نمایی از داده که برای Query/UI بهینه شده و ممکن است از چند Entity ساخته شود. Customer 360 در v0.6 یک Read Model است.

### Identity Resolution
تشخیص اینکه یک Identity خارجی متعلق به کدام Customer داخلی است.

### Cross-channel Merge
اتصال چند Identity از کانال‌های مختلف به یک Customer با شواهد معتبر مثل Phone/Email verified.

### Identity Collision
وقتی دو رکورد یا دو Customer مدعی یک Identity یا اطلاعات مشترک باشند.

---

## Attribution

### Attribution
نسبت‌دادن یک Outcome مثل Lead یا Sale به Source، Channel، Campaign یا Content.

### Touchpoint
یک تماس قابل ثبت در Customer Journey؛ مثل دیدن Content، ارسال DM، کلیک Campaign یا ایجاد Lead.

### First-touch Attribution
تمام اعتبار Conversion به اولین Touchpoint داده می‌شود.

### Last-touch Attribution
تمام اعتبار به آخرین Touchpoint قبل از Conversion داده می‌شود.

### Multi-touch Attribution
اعتبار بین چند Touchpoint تقسیم می‌شود.

### Source
منبع ایجاد Touchpoint؛ مثل `instagram_reel`, `telegram`, `website_form`.

### Campaign
نام یا شناسه کمپینی که Touchpoint به آن وابسته است.

### Content Attribution
اتصال Touchpoint یا Lead به `content_id` مشخص برای اندازه‌گیری اثر محتوا.

### Revenue Attribution
اتصال Revenue به Touchpoint/Content/Campaign. در v0.6 پایه Attribution ساخته شده اما Revenue model کامل هنوز Gate بعدی است.

---

## Follow-up Safety

### Stop Condition
شرطی که با رخ دادن آن Sequence پیگیری باید متوقف شود.

### Customer Replied Stop
وقتی Customer پاسخ واقعی می‌دهد، Follow-upهای pending فروش نباید کورکورانه ادامه پیدا کنند.

### Closed Lead
Lead با وضعیت `won` یا `lost`. ایجاد Follow-up جدید برای آن مجاز نیست.

### Manual Stop
توقف دستی Follow-up توسط اپراتور.

### Opt-out
درخواست Customer برای توقف پیام‌های بازاریابی/پیگیری. مدل Consent کامل هنوز باید اضافه شود.

### Suppression
قانون جلوگیری از ارسال پیام به Customer یا Identity خاص.

---

## Human Operations

### Human Handoff
انتقال Conversation به اپراتور انسانی.

### Human Outbound
پیامی که اپراتور نوشته اما همچنان از Outbound Pipeline استاندارد عبور می‌کند؛ بنابراین قابل Audit و Retry است.

### Approval
تصمیم انسانی برای مجاز کردن AI Draft.

### Edit-before-approve
ویرایش AI Draft قبل از Approval؛ متن نهایی Outbound همان نسخه ویرایش‌شده است.

### Rejection
رد Draft بدون ساخت Outbound Message.

---

# اصطلاحات اجباری v0.6

هر عضو تیم باید بتواند این موارد را با مثال توضیح دهد:

`Intent Classifier`, `Confidence`, `Deterministic Policy`, `Fail-Closed`, `AI Draft`, `Review Queue`, `Outbound Message`, `Delivery Context`, `Channel Adapter`, `At-least-once`, `Customer 360`, `Touchpoint`, `Attribution`, `Stop Condition`, `Human Outbound`.
