export default function HomePage() {
  return (
    <main dir="rtl" style={{ minHeight: '100vh', padding: '48px 20px', fontFamily: 'system-ui, sans-serif', background: '#f5f7f6', color: '#10231d' }}>
      <section style={{ maxWidth: 1040, margin: '0 auto' }}>
        <p style={{ opacity: 0.55 }}>Risheh Engage · v0.7 · Grounded AI + Production Hardening</p>
        <h1 style={{ fontSize: 'clamp(38px,7vw,72px)', lineHeight: 1.05, letterSpacing: '-.045em', marginBottom: 20 }}>Content → Conversation → Grounded AI → Customer → Conversion</h1>
        <p style={{ maxWidth: 820, lineHeight: 1.9, fontSize: 18, opacity: .75 }}>
          پلتفرم عملیاتی محتوا و ارتباط با مشتری با Grounded AI، Unified Inbox، Verified Identity، Consent، SLA، Customer 360، Outbound Delivery و Attribution. PostgreSQL مالک Product State است و n8n فقط Automation و Channel Adapter را اجرا می‌کند.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', margin: '28px 0 36px' }}>
          <a href="/studio" style={{ background: '#174A3A', color: '#fff', borderRadius: 14, padding: '12px 18px', textDecoration: 'none' }}>Content Studio</a>
          <a href="/inbox" style={{ background: '#12304A', color: '#fff', borderRadius: 14, padding: '12px 18px', textDecoration: 'none' }}>Unified Inbox</a>
          <a href="/ai-queue" style={{ background: '#312e81', color: '#fff', borderRadius: 14, padding: '12px 18px', textDecoration: 'none' }}>AI Review Queue</a>
          <a href="/knowledge" style={{ background: '#fff', color: '#174A3A', border: '1px solid rgba(23,74,58,.25)', borderRadius: 14, padding: '12px 18px', textDecoration: 'none' }}>Knowledge Sources</a>
          <a href="http://localhost:8000/docs" style={{ color: '#174A3A', border: '1px solid rgba(23,74,58,.25)', borderRadius: 14, padding: '12px 18px', textDecoration: 'none' }}>OpenAPI Local</a>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(210px,1fr))', gap: 12 }}>
          {[
            ['Grounded AI', 'Knowledge retrieval + evidence؛ بدون Evidence پاسخ Grounded ساخته نمی‌شود'],
            ['Knowledge Base', 'Source، Chunk، Retrieval و Evidence برای FAQ/Policy/Product'],
            ['Verified Identity', 'Merge چند کانال فقط بعد از Verification؛ نه با حدس'],
            ['Consent', 'Marketing/Sales follow-up با Consent صریح و قابل لغو'],
            ['SLA + Escalation', 'First response deadline، Breach و escalation level'],
            ['Provider Credentials', 'Credential رمز‌شده و Workspace-scoped'],
            ['Unified Inbox', 'Conversationهای چند کانال در مدل داخلی واحد'],
            ['AI Review Queue', 'Draft، Evidence، Edit، Approve و Reject'],
            ['Customer 360', 'Identity، Conversation، Lead، Attribution و Follow-up'],
            ['Attribution', 'Touchpoint summary بر اساس Channel، Source و Event'],
            ['Reliable Outbox', 'Lock، Retry، Backoff و Dead Letter'],
            ['Adapter Architecture', 'Telegram عملی؛ Instagram/WhatsApp پشت Contract مشترک'],
          ].map(([title, description]) => (
            <article key={title} style={{ padding: 18, borderRadius: 18, border: '1px solid rgba(15,23,42,.1)', background: '#fff' }}>
              <strong>{title}</strong>
              <p style={{ opacity: .65, lineHeight: 1.7, marginBottom: 0 }}>{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
