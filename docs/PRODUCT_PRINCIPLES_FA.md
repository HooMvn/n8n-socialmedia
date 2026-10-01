# اصول محصول Risheh Engage

این سند قوانین پایه‌ای محصول را مشخص می‌کند. هر Feature، Workflow و تصمیم طراحی باید با این اصول سازگار باشد.

## 1. ما Workflow نمی‌فروشیم؛ Outcome می‌فروشیم

کاربر نباید برای استفاده از محصول n8n بلد باشد.

ارزش محصول باید در نتیجه دیده شود:

- محتوای منظم‌تر
- پاسخ سریع‌تر
- لید کمتر گم‌شده
- Follow-up بهتر
- Conversion قابل‌اندازه‌گیری

## 2. Content بدون Conversation ناقص است

تولید محتوا هدف نهایی نیست.

هر Content Item باید بتواند به Interaction، Conversation، Lead و در نهایت Conversion متصل شود.

## 3. Human Control پیش‌فرض است

AI برای سرعت و کیفیت کمک می‌کند؛ مسئولیت نهایی عملیات حساس با انسان است.

هیچ Auto-publish یا Auto-reply حساس بدون policy شفاف فعال نمی‌شود.

## 4. AI Copilot است، نه مالک سیستم

AI می‌تواند:

- پیشنهاد دهد
- خلاصه کند
- طبقه‌بندی کند
- Draft بسازد
- Lead را score کند

اما نباید بدون Rule معتبر:

- permission بدهد
- refund کند
- commitment مالی ایجاد کند
- داده امنیتی تغییر دهد
- state حساس را تغییر دهد

## 5. یک Customer، چند Channel

Instagram ID، Telegram ID، شماره موبایل و ایمیل «مشتری» نیستند؛ Identityهای مختلف یک Customer هستند.

هدف، ساخت Customer 360 است.

## 6. هر Automation باید قابل توقف باشد

کاربر یا اپراتور باید بتواند:

- workflow را pause کند
- follow-up را stop کند
- automation را replay کند
- execution history را ببیند

## 7. Automation نباید Spam تولید کند

هر sequence باید stop condition، rate limit، opt-out و frequency policy داشته باشد.

## 8. Approval یک Feature اصلی است

Review و Approval نباید workaround با Telegram message یا Google Sheet باشد؛ باید بخشی از Domain محصول باشد.

## 9. Source of Truth واحد

Business data در PostgreSQL است.

Spreadsheet، n8n static data یا provider خارجی مرجع نهایی سیستم نیستند.

## 10. Integrationها Plug-in هستند

Instagram، Telegram، WhatsApp یا AI provider باید قابل جایگزینی باشند.

محصول نباید به یک API خاص وابسته بماند.

## 11. Multi-tenant از روز اول

حتی اگر اولین نصب فقط برای یک Business باشد، مدل داده و API باید Workspace-aware باشند.

## 12. Privacy by Design

فقط داده لازم ذخیره می‌شود.

دسترسی، retention و حذف داده باید قابل مدیریت باشد.

## 13. Explainability برای Automation

کاربر باید بفهمد:

- چرا این Lead ساخته شد؟
- چرا این پیام به Human فرستاده شد؟
- چرا Follow-up اجرا شد؟
- چرا محتوا Publish نشد؟

سیستم نباید Black Box باشد.

## 14. Failure یک State معتبر است

Failed نباید فقط در log گم شود.

هر عملیات خارجی باید status و recovery path داشته باشد.

## 15. UX باید عملیات را ساده کند

کاربر قرار نیست Automation Graph ببیند.

UI باید بر اساس Task طراحی شود:

- محتوای امروز
- پیام‌های نیازمند پاسخ
- لیدهای نیازمند پیگیری
- Approvalهای منتظر
- خطاهای نیازمند اقدام

## 16. Progressive Automation

سطح Automation باید قابل افزایش باشد:

```text
Manual
  ↓
AI Suggestion
  ↓
AI Draft + Human Approval
  ↓
Auto-execution for low risk
```

اعتماد سیستم به‌تدریج ساخته می‌شود.

## 17. Metrics قبل از AI Magic

هر Feature باید KPI مشخص داشته باشد.

اگر نمی‌توانیم تأثیر Feature را بسنجیم، احتمالاً هنوز ارزش محصولی آن روشن نیست.

## 18. Vertical-ready, Core-first

Core عمومی باقی می‌ماند؛ تفاوت صنایع از طریق Configuration، Template و Adapter ایجاد می‌شود.

نسخه‌های آینده می‌توانند شامل:

- Ecommerce
- Clinic
- Legal
- Education
- Real Estate

باشند بدون Fork کردن Core.

## 19. API-first

UI، n8n و Integrationها باید از قراردادهای API مشخص استفاده کنند.

Business logic در UI کپی نمی‌شود.

## 20. Security یک Gate است

Feature بدون tenant isolation، authorization، secret management و audit مناسب Done نیست.

---

## اصل طلایی

> **Content → Conversation → Conversion**

هر تصمیم محصول باید حداقل یکی از این سه مرحله را بهتر کند یا اتصال میان آن‌ها را قوی‌تر سازد.
