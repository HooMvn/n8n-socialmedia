# دانشنامه تخصصی Customer Communication — Risheh Engage

این فایل مکمل `TECHNICAL_GLOSSARY_FA.md` است و قبل از کار روی Unified Inbox، LeadOps یا Channel Adapter باید خوانده شود.

## Inbound Message
پیامی که از بیرون سیستم وارد می‌شود؛ مثلاً Telegram DM، Instagram DM یا Website Chat.

## Outbound Message
پیامی که سیستم، AI یا اپراتور به مشتری ارسال می‌کند.

## Channel
مسیر ارتباطی مثل `telegram`, `instagram`, `whatsapp`, `website`, `email`.

## Channel Adapter
لایه‌ای که فرمت اختصاصی Provider را به Contract استاندارد Risheh Engage تبدیل می‌کند. Core نباید Telegram-specific یا Instagram-specific باشد.

## External User ID
شناسه کاربر در Provider. این مقدار به تنهایی Customer نیست؛ فقط یک Identity کانالی است.

## External Message ID
شناسه یکتای Message در Provider. برای Deduplication webhook استفاده می‌شود.

## Customer Identity
رابط بین یک حساب خارجی و Customer داخلی. یک Customer می‌تواند چند Identity داشته باشد.

## Identity Resolution
فرآیند تشخیص اینکه چند Identity متعلق به یک Customer هستند. V0.5 بر اساس Channel + External User ID عمل می‌کند؛ merge پیشرفته در آینده اضافه می‌شود.

## Customer 360
نمای یکپارچه Customer شامل تمام Identityها، Conversationها، Messages، Lead، Follow-up، Orders و Attribution.

## Unified Inbox
نمای واحد Conversationهای چند کانال. Unified یعنی داده‌ها استاندارد شده‌اند، نه اینکه Providerها حذف شوند.

## Conversation
Thread منطقی پیام‌ها بین Customer و کسب‌وکار در یک Channel.

## Conversation State
وضعیت Thread: `open`, `waiting_human`, `resolved`, `closed`.

## Message Direction
`inbound` یعنی مشتری → سیستم؛ `outbound` یعنی سیستم/تیم → مشتری.

## Author Type
منبع پیام: `customer`, `ai`, `human`, `system`.

## Intent
هدف احتمالی پیام؛ مثل pricing، support، complaint، sales_interest یا appointment.

## Intent Classification
تبدیل متن پیام به یک Intent ساختاریافته. می‌تواند Rule-based یا AI-assisted باشد.

## Confidence Score
عدد 0 تا 100 برای میزان اطمینان طبقه‌بندی. Confidence نباید به تنهایی مجوز اقدام حساس باشد.

## Human Handoff
انتقال Conversation از Automation/AI به اپراتور انسانی.

## Assignment
اختصاص Conversation، Lead یا Follow-up به User مشخص.

## Lead
Customer دارای سیگنال تجاری که باید در Pipeline فروش مدیریت شود.

## Lead Qualification
بررسی ارزش و آمادگی Lead برای فروش.

## Lead Score
امتیاز اولویت 0..100. در v0.5 امتیاز >=70 Lead جدید را Qualified می‌کند؛ این Rule موقت و قابل جایگزینی است.

## Sales Pipeline
State machine لید: `new → qualified → contacted → proposal → won/lost`.

## Follow-up
تعهد زمان‌دار برای پیگیری Lead. Follow-up با پیام خودکار یکی نیست؛ ممکن است Task انسانی باشد.

## Stop Condition
شرط توقف Automation؛ مثل پاسخ مشتری، Won/Lost شدن Lead، Opt-out یا Human Stop.

## Deduplication
جلوگیری از ثبت دوباره یک Event/Message تکراری.

## Idempotent Ingestion
اگر Provider یک webhook را چند بار بفرستد، State نهایی سیستم همان یک Message باقی بماند.

## Webhook Replay
ارسال دوباره همان Event توسط Provider به‌علت timeout یا retry. باید رفتار عادی فرض شود، نه Exception عجیب.

## SLA
زمان هدف برای پاسخ یا رسیدگی. در نسخه‌های بعد برای Inbox و Escalation استفاده می‌شود.

## Escalation
بالا بردن سطح رسیدگی وقتی SLA رد شده یا پیام حساس است.

## Sentiment
برداشت مثبت/منفی/خنثی از متن. Sentiment با Intent فرق دارد؛ شکایت یک Intent است، عصبانیت می‌تواند Sentiment باشد.

## PII
Personally Identifiable Information؛ اطلاعاتی مثل شماره تلفن و ایمیل که نیاز به کنترل دسترسی، retention و logging مناسب دارند.

## Data Minimization
فقط اطلاعاتی را ذخیره کنیم که برای هدف محصول لازم است.

## Tenant Scope
تمام Queryها و Mutationهای Business باید داخل Workspace انجام شوند. `customer_id` بدون `workspace_id` مرز امنیتی کافی نیست.

## Source Attribution
ثبت اینکه Lead از کدام Channel/Content/Campaign آمده. در v0.5 فقط source_channel داریم؛ Content/Campaign attribution فاز بعد است.

## AI Draft Reply
پاسخی که AI پیشنهاد می‌دهد ولی بسته به Risk Policy ممکن است نیاز به Human Approval داشته باشد.

## Guardrail
قانون یا کنترل فنی برای جلوگیری از اقدام نامعتبر AI؛ مثل Handoff در confidence پایین یا ممنوعیت تعهد مالی خودکار.

## تیم قبل از شروع باید بتواند توضیح دهد

`Customer vs Identity`, `Conversation vs Message`, `Inbound vs Outbound`, `Intent vs Sentiment`, `Lead vs Customer`, `Follow-up vs Automation`, `Deduplication`, `Handoff`, `Tenant Scope`, `Channel Adapter`.
