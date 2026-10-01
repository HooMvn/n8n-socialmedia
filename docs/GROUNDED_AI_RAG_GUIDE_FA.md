# راهنمای Grounded AI و RAG — Risheh Engage v0.7

## چرا این فایل مهم است؟
در v0.6 مدل می‌توانست از Brand Context پاسخ پیشنهادی بسازد. در v0.7 هدف این است که پاسخ به دانش ثبت‌شده در Workspace تکیه کند و Evidence قابل مشاهده داشته باشد.

## معماری

```text
Knowledge Source
   ↓
Chunking
   ↓
KnowledgeChunk
   ↓
Retrieval
   ↓
Relevant Chunks
   ↓
Prompt Context
   ↓
AI Draft
   ↓
RetrievalEvidence
   ↓
Human Review
```

## KnowledgeSource
یک منبع معتبر کسب‌وکار مثل:
- FAQ
- اطلاعات محصول
- Policy
- متن سایت
- سند داخلی
- راهنمای خدمات

## Chunk
سند بزرگ به بخش‌های کوچک‌تر تقسیم می‌شود تا Retrieval دقیق‌تر و Context محدودتر باشد.

v0.7 از Chunk overlap استفاده می‌کند تا اطلاعاتی که روی مرز دو Chunk قرار می‌گیرند از بین نروند.

## Retrieval فعلی
v0.7 یک Retrieval deterministic بر اساس lexical overlap دارد. مزیت آن برای Foundation:
- قابل تست
- بدون Provider خارجی
- deterministic
- ساده برای درک تیم

اما برای Knowledge Base بزرگ، Semantic/Vector Retrieval در فاز بعد مناسب‌تر است.

## Retrieval Evidence
برای هر AIDraft ذخیره می‌کنیم:
- کدام Chunk استفاده شد
- Rank آن چند بود
- Score آن چقدر بود

این یعنی بعداً Review UI می‌تواند نشان دهد پاسخ AI به کدام منبع تکیه داشته است.

## Grounded Draft Rule
اگر هیچ منبع مرتبط پیدا نشود:

```text
No Evidence
→ AI Draft blocked
→ Human Review Required
```

سیستم نباید برای پر کردن خلأ، Fact اختراع کند.

## RAG چیست؟
Retrieval-Augmented Generation یعنی قبل از Generation، اطلاعات معتبر مرتبط Retrieve و به مدل داده شود.

RAG دو بخش مستقل دارد:
1. Retrieval Quality
2. Generation Quality

مدل قوی با Retrieval بد هنوز می‌تواند پاسخ بد بدهد.

## Citation vs Evidence
Evidence یعنی سیستم می‌داند کدام Chunk به مدل داده شده است. Citation یعنی این Evidence به شکل قابل فهم به Reviewer یا Customer نمایش داده شود. v0.7 Evidence را ذخیره می‌کند؛ Citation UX کامل هنوز Gate بعدی است.

## Prompt Injection
Knowledge Source داده است، نه دستور Trusted. متن سند نباید بتواند System Policy را Override کند.

## تمرین تیم
1. یک FAQ به Knowledge Source اضافه کنید.
2. چند سؤال مرتبط و نامرتبط ایجاد کنید.
3. Retrieval score را مقایسه کنید.
4. سؤال نامرتبط باید Grounded Draft را Block کند.
5. Evidence Draft را بررسی کنید.

## Gate توسعه‌دهنده
قبل از تغییر RAG باید بتواند توضیح دهد:
- Chunking چیست؟
- Retrieval با Generation چه فرقی دارد؟
- Evidence چه کاربردی دارد؟
- چرا No Evidence باید Fail Closed باشد؟
- Semantic Retrieval چه مزیتی نسبت به Lexical دارد؟
