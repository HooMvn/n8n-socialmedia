# مسیر آموزشی v0.7 — Risheh Engage

این مسیر برای اعضای تیمی است که می‌خواهند روی Grounded AI، Multi-channel، Customer Identity و Production Hardening کار کنند.

## مرحله 1 — مرور معماری
مطالعه:
- README.md
- docs/ARCHITECTURE_FA.md
- docs/AI_CUSTOMER_COMMUNICATION_GUIDE_FA.md

باید بتوانید توضیح دهید:
```text
Provider → Adapter → Inbound Contract → Domain → Policy → Outbound → Provider
```

## مرحله 2 — Grounded AI
مطالعه:
- docs/GROUNDED_AI_RAG_GUIDE_FA.md
- docs/PRODUCTION_HARDENING_GLOSSARY_FA.md

تمرین:
1. یک FAQ بسازید.
2. آن را به Knowledge Source تبدیل کنید.
3. سؤال مرتبط بپرسید.
4. Retrieval Evidence را بررسی کنید.
5. سؤال نامرتبط بپرسید و Fail-Closed را ببینید.

## مرحله 3 — Retrieval Engineering
مفاهیم:
- Chunking
- Chunk overlap
- Lexical Retrieval
- Semantic Retrieval
- Embedding
- Vector Search
- Reranking
- Evidence
- Citation

تمرین:
سه Query طراحی کنید که Lexical Retrieval در آن ضعیف باشد و توضیح دهید Semantic Retrieval چرا بهتر است.

## مرحله 4 — Identity Engineering
مفاهیم:
- Customer
- CustomerIdentity
- Verification
- Merge
- Conflict
- Split/Audit

قانون:
Similarity ≠ Identity Proof

تمرین:
دو Customer با نام مشابه بسازید. بدون Verification نباید Merge شوند.

## مرحله 5 — Consent / Privacy
مفاهیم:
- Purpose limitation
- Opt-in
- Opt-out
- Suppression
- PII
- Retention
- Redaction

تمرین:
Marketing Outbound بدون Consent باید Block شود.

## مرحله 6 — SLA و Escalation
مفاهیم:
- First Response SLA
- Resolution SLA
- Breach
- Escalation Level
- Human Queue

تمرین:
Conversation با SLA کوتاه بسازید و Breach evaluator را تست کنید.

## مرحله 7 — Provider Credentials
مفاهیم:
- Secret
- Encryption at Rest
- Key Rotation
- Workspace Scope
- Secret Manager
- Credential Health

تمرین:
بررسی کنید API لیست Credentials هرگز Secret را برنمی‌گرداند.

## مرحله 8 — Multi-channel Adapter
مطالعه:
- automation/MULTICHANNEL_ADAPTERS_V07_FA.md

باید بتوانید توضیح دهید:
- Channel با Provider چه فرقی دارد؟
- چرا Core نباید Meta-specific field داشته باشد؟
- Delivery Context چیست؟
- Retryable Provider Error چیست؟

## مرحله 9 — Attribution
مفاهیم:
- Touchpoint
- Source
- Campaign
- First Touch
- Last Touch
- Multi-touch
- Revenue Attribution

تمرین:
یک Customer با سه Touchpoint بسازید و summary را بررسی کنید.

## مرحله 10 — Security Review
قبل از PR:
- Secret در Log نیست.
- Workspace ID روی تمام Queryهای حساس enforce شده.
- Merge فقط با Verification است.
- Marketing Consent enforce شده.
- AI بدون Evidence پاسخ Grounded تولید نمی‌کند.
- Provider token در Workflow export وجود ندارد.

# Gate ورود به Task v0.7
توسعه‌دهنده باید بتواند بدون فایل پاسخ دهد:
1. Grounded AI چیست؟
2. Evidence با Citation چه فرقی دارد؟
3. Lexical و Semantic Retrieval چه فرقی دارند؟
4. چرا Identity Merge خطرناک است؟
5. Purpose Limitation چیست؟
6. SLA Breach چه Eventی ایجاد می‌کند؟
7. Encryption و Hashing چه فرقی دارند؟
8. Workspace-scoped Credential چرا لازم است؟
9. Provider Adapter چه چیزی را Normalize می‌کند؟
10. Revenue Attribution چرا از Touchpoint Foundation جداست؟
