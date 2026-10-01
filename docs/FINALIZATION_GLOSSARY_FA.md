# دانشنامه اصطلاحات مرحله نهایی — Risheh Engage v0.8

این فایل برای فهم اصطلاحاتی است که در مرحله Production Readiness استفاده می‌شوند.

## Release Candidate (RC)
نسخه‌ای که Feature اصلی جدید نمی‌گیرد و فقط برای تست، Hardening و رفع باگ آماده می‌شود.

## Production Readiness
آمادگی فنی و عملیاتی برای اجرای واقعی سیستم با داده و کاربر واقعی؛ شامل امنیت، تست، مانیتورینگ، Backup و Rollback.

## Release Gate
شرطی که تا پاس نشود Release نباید جلو برود. مثال: Migration روی PostgreSQL واقعی باید موفق باشد.

## Smoke Test
تست سریع بعد از Deploy برای بررسی اینکه مسیرهای حیاتی سیستم بالا هستند. Smoke Test جای Integration/E2E را نمی‌گیرد.

## Integration Test
تستی که چند جزء واقعی مثل Application + PostgreSQL را با هم بررسی می‌کند.

## End-to-End Test (E2E)
تست یک Journey کامل از دید کاربر یا سیستم، مثلاً Inbound → Customer → AI Draft → Review → Outbound.

## Health Check
نشان می‌دهد Process زنده است. لزوماً به معنی آماده بودن dependencyها نیست.

## Readiness Check
نشان می‌دهد سرویس برای دریافت Traffic آماده است. در Engage اتصال DB هم بررسی می‌شود.

## Observability
توانایی فهم وضعیت داخلی سیستم از طریق Logs، Metrics و Trace/Correlation context.

## Metric
اندازه‌گیری عددی مثل تعداد Request، Latency یا Error Rate.

## Latency
زمان لازم برای انجام درخواست. معمولاً p50/p95/p99 مهم‌تر از Average هستند.

## Request ID / Correlation ID
شناسه‌ای برای دنبال‌کردن یک Request بین سرویس‌ها و Logها.

## p95
مقداری که 95٪ درخواست‌ها سریع‌تر از آن انجام شده‌اند. برای Latency معیار عملی بهتری از Average است.

## Backup
نسخه قابل بازیابی از داده. Backup بدون تست Restore فقط «فایل» است، نه تضمین Recovery.

## Restore Drill
تمرین واقعی بازیابی Backup روی محیط امن برای اثبات اینکه Backup قابل استفاده است.

## RPO — Recovery Point Objective
حداکثر مقدار داده‌ای که کسب‌وکار می‌پذیرد در حادثه از دست برود.

## RTO — Recovery Time Objective
حداکثر زمان قابل قبول برای بازگرداندن سرویس.

## Rollback
بازگشت Application به نسخه قبلی بعد از Release ناموفق.

## Roll Forward
رفع مشکل با Release اصلاحی جدید، به‌جای بازگشت نسخه.

## Immutable Release
Release با Revision/Tag مشخص که بعد از ساخت تغییر نمی‌کند.

## Migration Gate
قانونی که Migration قبل از Start نسخه جدید باید با موفقیت اجرا شود.

## Fail-Closed
وقتی Dependency یا Policy نامعتبر است، سیستم Action حساس را انجام نمی‌دهد.

## Secret Rotation
تعویض دوره‌ای یا اضطراری Secret بدون شکستن سیستم.

## Least Privilege
هر سرویس یا کاربر فقط کمترین Permission لازم را داشته باشد.

## Rate Limiting
محدودکردن تعداد Request برای جلوگیری از Abuse، Brute Force یا فشار روی Provider.

## Dead Letter Queue / State
جایی برای Eventهایی که بعد از Retryهای محدود همچنان Fail شده‌اند و نیاز به بررسی دارند.

## Retry Budget
حد و سیاست Retry؛ Retry نامحدود می‌تواند Incident را شدیدتر کند.

## Runbook
دستورالعمل عملیاتی مرحله‌به‌مرحله برای Deploy، Incident، Backup یا Provider failure.

## Incident
اختلالی که Availability، Integrity، Security یا عملکرد کسب‌وکار را تحت تأثیر قرار می‌دهد.

## Postmortem
بررسی بعد از Incident برای فهم علت، اثر و اقدام اصلاحی؛ هدف یادگیری سیستم است نه سرزنش فرد.

## SLO — Service Level Objective
هدف داخلی قابلیت اطمینان، مثلاً 99.9٪ Availability.

## SLA — Service Level Agreement
تعهد سطح سرویس به مشتری یا بین بخش‌ها. SLA با SLO یکی نیست.

## Error Budget
مقدار Fail قابل قبول در بازه زمانی بر اساس SLO.

## Pilot
اجرای محدود محصول با مشتری/Workspace واقعی برای اثبات ارزش و پایداری قبل از Rollout گسترده.

## Production-like Environment
محیطی که تا حد ممکن به Production شبیه است: DB واقعی، Migration واقعی، Network و Config نزدیک.

## Feature Freeze
توقف اضافه‌کردن Feature جدید در مرحله Release تا تمرکز روی Stability بماند.

## Definition of Release Ready
مجموعه شرایط قابل سنجش که نشان می‌دهد Release برای Pilot آماده است؛ نه احساس یا حدس تیم.
