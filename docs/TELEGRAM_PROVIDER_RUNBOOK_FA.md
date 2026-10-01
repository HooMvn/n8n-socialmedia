# Runbook تلگرام — Risheh Engage

## هدف
این Runbook برای اولین Publish واقعی روی Telegram است و باید فقط با Bot/Chat تست اجرا شود.

## 1. Bot
از BotFather یک Bot تست بسازید و Token را فقط در Secret/Environment نگه دارید.

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_DEFAULT_CHAT_ID=...
```

Token را هرگز در Repository، Screenshot یا Workflow JSON Commit نکنید.

## 2. بالا آوردن Stack

```bash
docker compose up --build
```

بررسی:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 3. Import Workflow
در n8n فایل زیر را Import کنید:

`automation/workflows/telegram_publish_v1.json`

Workflow باید با نام زیر دیده شود:

`ENGAGE__PUBLISH__TELEGRAM__V1`

قبل از Active کردن بررسی کنید:

- webhook path = `risheh-engage-publish`
- Environment access فعال است
- Token و Chat ID در Environment هستند
- `RISHEH_API_BASE_URL=http://api:8000`
- `RISHEH_AUTOMATION_SECRET` با Backend یکی است

## 4. فعال‌سازی
Workflow را Active کنید. Worker به URL زیر Event تحویل می‌دهد:

`N8N_PUBLISH_WEBHOOK_URL`

در Docker Compose مقدار داخلی آن:

`http://n8n:5678/webhook/risheh-engage-publish`

## 5. اجرای Studio

`http://localhost:3000/studio`

مسیر:

1. Register
2. Create Workspace
3. Save Brand
4. Create Telegram Draft
5. Submit Review
6. Approve
7. Publish Request

## 6. انتظار موفق

بعد از Publish Request:

```text
Publication = pending
Outbox = pending
↓
Worker claims event
↓
Outbox = processing
↓
n8n sends Telegram message
↓
Callback to API
↓
Publication = published
Content = published
Outbox = delivered
```

## 7. تست Failure
برای تست Retry می‌توانید موقتاً URL n8n را اشتباه کنید یا Workflow را غیرفعال کنید.

انتظار:

- attempt_count افزایش پیدا کند
- last_error ثبت شود
- next_attempt_at در آینده قرار بگیرد
- Event دوباره pending شود

بعد از سقف تلاش:

`dead_letter`

## 8. هشدار Duplicate
Telegram Bot API برای `sendMessage` idempotency key بومی ندارد. اگر Telegram پیام را ارسال کند ولی Callback شکست بخورد، retry ممکن است پیام تکراری بسازد.

برای Production این مورد باید با Provider Operation Ledger / Dedup Store بسته شود.

## 9. معیار پذیرش Live Smoke

- فقط یک پیام تست دریافت شود
- Publication به published برسد
- Content به published برسد
- external_id برابر message_id تلگرام ثبت شود
- Outbox delivered شود
- Secret در هیچ Log عمومی چاپ نشود

نتیجه Live Smoke باید با تاریخ و محیط اجرا در `docs/IMPLEMENTATION_STATUS_FA.md` ثبت شود.
