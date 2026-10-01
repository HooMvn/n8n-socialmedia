# Contributing to Risheh Engage

این سند قواعد پایه توسعه پروژه را مشخص می‌کند.

## قبل از شروع هر Feature

1. مسئله کاربر و Outcome را مشخص کنید.
2. Domain مالک Feature را تعیین کنید.
3. مشخص کنید آیا API contract جدید نیاز است یا خیر.
4. Integration خارجی را از Core جدا نگه دارید.
5. Failure path و retry را قبل از happy path در نظر بگیرید.
6. مشخص کنید آیا Feature به approval یا audit نیاز دارد.

## Branch Naming

```text
feat/<name>
fix/<name>
docs/<name>
refactor/<name>
chore/<name>
```

## Commit Convention

نمونه:

```text
feat(content): add approval transition
fix(inbox): deduplicate inbound messages
docs(architecture): document outbox strategy
```

## Pull Request Checklist

- [ ] Scope کوچک و مشخص است.
- [ ] Domain rule در n8n دفن نشده است.
- [ ] tenant scope رعایت شده است.
- [ ] validation server-side وجود دارد.
- [ ] happy path تست شده است.
- [ ] failure path تست شده است.
- [ ] integration idempotent است.
- [ ] log شامل secret/PII غیرضروری نیست.
- [ ] UI loading/empty/error state دارد.
- [ ] documentation لازم به‌روزرسانی شده است.

## Workflowهای n8n

هر Workflow باید:

- نام canonical داشته باشد.
- version کنترل‌شده داشته باشد.
- trigger مشخص داشته باشد.
- input/output contract مستند داشته باشد.
- timeout/retry policy داشته باشد.
- error path داشته باشد.
- secret hardcoded نداشته باشد.
- از business database به‌عنوان source of truth استفاده کند.

نام پیشنهادی:

```text
<domain>.<action>.v<major>
```

مثال:

```text
content.publish.v1
conversation.classify.v1
lead.followup.v1
```

## Definition of Done

Feature فقط وقتی Done است که قابل مشاهده، تست، بازیابی از خطا و مستندسازی شده باشد.

کدی که فقط روی سیستم توسعه‌دهنده کار می‌کند Done نیست.
