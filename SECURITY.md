# Security Baseline — Risheh Engage

امنیت بخشی از Definition of Done است، نه مرحله‌ای بعد از توسعه.

## 1. Secrets

- Token، API Key، Password و private credential داخل Git commit نمی‌شود.
- `.env` در gitignore قرار می‌گیرد.
- `.env.example` فقط نام متغیرها و مقدار امن نمونه دارد.
- Secretهای production از secret manager / environment امن خوانده می‌شوند.
- credentialهای provider باید قابل rotation باشند.

## 2. Authentication & Authorization

- Authorization در backend enforce می‌شود.
- مخفی کردن دکمه در UI امنیت محسوب نمی‌شود.
- تمام resourceهای tenant-owned با workspace scope خوانده می‌شوند.
- عملیات حساس audit می‌شوند.

## 3. Webhook Security

برای webhookهای خارجی در صورت پشتیبانی Provider:

- signature verification
- timestamp validation
- replay protection
- idempotency
- payload size limits
- rate limiting

الزامی است.

Webhook URL به‌تنهایی secret فرض نمی‌شود.

## 4. n8n

- Editor عمومی expose نمی‌شود.
- دسترسی production محدود است.
- credentialها در n8n credential store نگهداری می‌شوند، نه داخل workflow JSON.
- workflow export قبل از commit برای secret بررسی می‌شود.
- webhookهای داخلی با auth/signature محافظت می‌شوند.

## 5. Database

- PostgreSQL مستقیم روی اینترنت publish نمی‌شود.
- least privilege برای DB userها رعایت می‌شود.
- backup رمزگذاری‌شده و تست restore تعریف می‌شود.
- migrationهای destructive نیازمند review هستند.

## 6. PII

داده‌هایی مثل شماره موبایل، ایمیل و پیام‌های مشتری PII محسوب می‌شوند.

اصول:

- data minimization
- purpose limitation
- access control
- retention policy
- export/delete path
- عدم قرار دادن PII در log مگر ضرورت مشخص

## 7. AI Providers

قبل از ارسال داده به LLM:

- مشخص شود چه داده‌ای ضروری است.
- secret و credential حذف شود.
- داده حساس غیرضروری redaction شود.
- provider و policy آن قابل configuration باشد.

خروجی LLM untrusted input محسوب می‌شود.

## 8. Prompt Injection

محتوای مشتری، وب‌سایت یا Knowledge Source ممکن است malicious instruction داشته باشد.

AI نباید بر اساس محتوای ورودی بتواند:

- secret بخواند.
- tool غیرمجاز اجرا کند.
- permission تغییر دهد.
- destructive action انجام دهد.

Tool access باید allowlist و policy-based باشد.

## 9. Logging

ممنوع در log:

- password
- bearer token
- API key
- full provider credential
- session secret

Errorها باید correlation ID داشته باشند.

## 10. Dependency Security

در CI باید حداقل:

- dependency audit
- secret scanning
- static checks
- container vulnerability scan در مسیر production

وجود داشته باشد.

## 11. Incident Readiness

برای production باید مشخص باشد:

- چگونه credential revoke می‌شود.
- چگونه integration disable می‌شود.
- چگونه workflow pause می‌شود.
- چگونه affected workspace پیدا می‌شود.
- چگونه audit trail بررسی می‌شود.

## 12. Security Release Gate

Feature حساس بدون موارد زیر Release نمی‌شود:

- [ ] tenant authorization
- [ ] server-side validation
- [ ] idempotency در external mutation
- [ ] secret safety
- [ ] auditability
- [ ] failure handling
- [ ] abuse/rate-limit consideration
- [ ] AI action policy در صورت استفاده از AI
