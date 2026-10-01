'use client';

import { useEffect, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type Conversation = {
  id: string;
  customer_id: string;
  channel: string;
  status: string;
  assigned_user_id?: string | null;
  intent?: string | null;
  intent_confidence?: number | null;
  last_message_at: string;
};

type Message = {
  id: string;
  author_type: string;
  direction: string;
  body: string;
  created_at: string;
};

const card: React.CSSProperties = {
  border: '1px solid rgba(15,23,42,.1)',
  borderRadius: 20,
  background: '#fff',
  boxShadow: '0 14px 42px rgba(15,23,42,.05)',
};

const input: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', padding: '11px 12px', borderRadius: 12,
  border: '1px solid rgba(15,23,42,.15)', font: 'inherit',
};

const action: React.CSSProperties = {
  border: 0, borderRadius: 10, padding: '9px 12px', background: '#174A3A', color: '#fff', cursor: 'pointer',
};

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
  return body as T;
}

export default function InboxPage() {
  const [token, setToken] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [reply, setReply] = useState('');
  const [log, setLog] = useState('توکن و Workspace را وارد کنید.');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setToken(localStorage.getItem('engage_token') ?? '');
    setWorkspaceId(localStorage.getItem('engage_workspace_id') ?? '');
  }, []);

  const activeCount = useMemo(
    () => conversations.filter((item) => item.status !== 'closed').length,
    [conversations],
  );
  const lastInbound = useMemo(
    () => [...messages].reverse().find((item) => item.direction === 'inbound'),
    [messages],
  );

  async function run(actionFn: () => Promise<void>) {
    try {
      setBusy(true);
      await actionFn();
    } catch (error) {
      setLog(error instanceof Error ? `خطا: ${error.message}` : 'خطای ناشناخته');
    } finally {
      setBusy(false);
    }
  }

  function loadInbox() {
    if (!token || !workspaceId) return;
    localStorage.setItem('engage_token', token);
    localStorage.setItem('engage_workspace_id', workspaceId);
    void run(async () => {
      const data = await request<Conversation[]>(`/api/v1/workspaces/${workspaceId}/inbox`, token);
      setConversations(data);
      setLog(`${data.length} مکالمه دریافت شد.`);
    });
  }

  function openConversation(conversation: Conversation) {
    void run(async () => {
      const data = await request<Message[]>(
        `/api/v1/workspaces/${workspaceId}/conversations/${conversation.id}/messages`, token,
      );
      setSelected(conversation);
      setMessages(data);
      setLog(`Conversation ${conversation.id} باز شد.`);
    });
  }

  function aiClassify() {
    if (!selected || !lastInbound) return;
    void run(async () => {
      const result = await request<{ intent: string; confidence: number; route: string; reason: string }>(
        `/api/v1/workspaces/${workspaceId}/conversations/${selected.id}/ai/classify`, token,
        { method: 'POST', body: JSON.stringify({ source_message_id: lastInbound.id }) },
      );
      const updated = { ...selected, intent: result.intent, intent_confidence: result.confidence, status: result.route === 'human_required' ? 'waiting_human' : selected.status };
      setSelected(updated);
      setConversations(items => items.map(item => item.id === updated.id ? updated : item));
      setLog(`AI Intent: ${result.intent} · ${result.confidence}% · route=${result.route} · ${result.reason}`);
    });
  }

  function createAIDraft() {
    if (!selected || !lastInbound) return;
    void run(async () => {
      const draft = await request<{ id: string; intent: string }>(
        `/api/v1/workspaces/${workspaceId}/conversations/${selected.id}/ai/drafts`, token,
        { method: 'POST', body: JSON.stringify({ source_message_id: lastInbound.id }) },
      );
      setLog(`AI Draft ساخته شد: ${draft.id}. برای Review به AI Queue بروید.`);
    });
  }

  function handoff() {
    if (!selected) return;
    void run(async () => {
      const updated = await request<Conversation>(
        `/api/v1/workspaces/${workspaceId}/conversations/${selected.id}/handoff`, token,
        { method: 'POST', body: JSON.stringify({ reason: 'نیاز به بررسی انسانی' }) },
      );
      setSelected(updated);
      setConversations(items => items.map(item => item.id === updated.id ? updated : item));
      setLog('Conversation به صف انسانی منتقل شد.');
    });
  }

  function createLead() {
    if (!selected) return;
    void run(async () => {
      const lead = await request<{ id: string; status: string; score: number }>(
        `/api/v1/workspaces/${workspaceId}/conversations/${selected.id}/lead`, token,
        { method: 'POST', body: JSON.stringify({ interest: 'درخواست فروش از Inbox', score: 80 }) },
      );
      setLog(`Lead: ${lead.id} · ${lead.status} · score=${lead.score}`);
    });
  }

  function sendHumanReply() {
    if (!selected || !reply.trim()) return;
    void run(async () => {
      const outbound = await request<{ id: string; status: string }>(
        `/api/v1/workspaces/${workspaceId}/conversations/${selected.id}/outbound`, token,
        {
          method: 'POST',
          body: JSON.stringify({ body: reply.trim(), idempotency_key: `human-${selected.id}-${Date.now()}` }),
        },
      );
      setReply('');
      setLog(`Human Outbound queued: ${outbound.id} · ${outbound.status}`);
    });
  }

  return (
    <main dir="rtl" style={{ minHeight: '100vh', background: '#f5f7f6', color: '#10231d', padding: '28px 16px 64px', fontFamily: 'system-ui, sans-serif' }}>
      <section style={{ maxWidth: 1180, margin: '0 auto' }}>
        <header style={{ marginBottom: 22 }}>
          <a href="/" style={{ color: '#174A3A', textDecoration: 'none' }}>← Risheh Engage</a>
          <p style={{ opacity: .55, marginBottom: 6 }}>v0.6 · AI-assisted Customer Communication</p>
          <h1 style={{ fontSize: 'clamp(32px,5vw,56px)', margin: 0 }}>Unified Inbox</h1>
          <p style={{ opacity: .7, lineHeight: 1.8 }}>Customer → Conversation → AI Intent → Policy → AI Draft / Human → Outbound → Lead.</p>
        </header>

        <section style={{ ...card, padding: 16, display: 'grid', gap: 12, gridTemplateColumns: '2fr 2fr auto', alignItems: 'end', marginBottom: 16 }}>
          <label>JWT Access Token<textarea value={token} onChange={e => setToken(e.target.value)} style={{ ...input, minHeight: 74, direction: 'ltr' }} /></label>
          <label>Workspace ID<input value={workspaceId} onChange={e => setWorkspaceId(e.target.value)} style={{ ...input, direction: 'ltr' }} /></label>
          <button disabled={busy || !token || !workspaceId} onClick={loadInbox} style={action}>بارگذاری Inbox</button>
        </section>

        <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'minmax(280px,.85fr) minmax(0,1.5fr)' }}>
          <aside style={{ ...card, overflow: 'hidden' }}>
            <div style={{ padding: 16, borderBottom: '1px solid rgba(15,23,42,.08)' }}>
              <strong>Conversationها</strong>
              <p style={{ margin: '6px 0 0', opacity: .6 }}>{activeCount} فعال · {conversations.length} کل</p>
            </div>
            <div style={{ maxHeight: 680, overflowY: 'auto' }}>
              {conversations.map(item => (
                <button key={item.id} onClick={() => openConversation(item)} style={{ width: '100%', textAlign: 'right', padding: 15, border: 0, borderBottom: '1px solid rgba(15,23,42,.06)', background: selected?.id === item.id ? '#edf4f1' : '#fff', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}><b>{item.channel}</b><span>{item.status}</span></div>
                  <small style={{ opacity: .6 }}>Customer: {item.customer_id.slice(0, 8)}…</small>
                  <div style={{ marginTop: 6, fontSize: 13 }}>{item.intent ? `${item.intent} · ${item.intent_confidence ?? '—'}%` : 'Intent ثبت نشده'}</div>
                </button>
              ))}
              {!conversations.length && <p style={{ padding: 18, opacity: .55 }}>هنوز Conversationی بارگذاری نشده.</p>}
            </div>
          </aside>

          <section style={{ ...card, minHeight: 560, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: 16, borderBottom: '1px solid rgba(15,23,42,.08)' }}>
              <strong>{selected ? `Conversation · ${selected.channel}` : 'یک Conversation انتخاب کنید'}</strong>
              {selected && <p style={{ margin: '6px 0 0', opacity: .6 }}>status={selected.status} · intent={selected.intent ?? '—'} · confidence={selected.intent_confidence ?? '—'}</p>}
            </div>
            <div style={{ padding: 18, flex: 1, overflowY: 'auto' }}>
              {messages.map(message => (
                <article key={message.id} style={{ maxWidth: '78%', margin: message.direction === 'inbound' ? '0 0 12px auto' : '0 auto 12px 0', padding: '12px 14px', borderRadius: 16, background: message.direction === 'inbound' ? '#edf4f1' : '#f0f2f5' }}>
                  <small style={{ opacity: .55 }}>{message.author_type}</small>
                  <p style={{ margin: '5px 0 0', lineHeight: 1.8 }}>{message.body}</p>
                </article>
              ))}
            </div>
            {selected && (
              <div style={{ padding: 14, borderTop: '1px solid rgba(15,23,42,.08)' }}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                  <button disabled={busy || !lastInbound} onClick={aiClassify} style={action}>AI Classify</button>
                  <button disabled={busy || !lastInbound} onClick={createAIDraft} style={{ ...action, background: '#312e81' }}>Generate AI Draft</button>
                  <a href="/ai-queue" style={{ ...action, textDecoration: 'none', background: '#4c1d95' }}>Review Queue</a>
                  <button disabled={busy} onClick={handoff} style={action}>Human Handoff</button>
                  <button disabled={busy} onClick={createLead} style={action}>Convert to Lead</button>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input value={reply} onChange={e => setReply(e.target.value)} placeholder="پاسخ انسانی…" style={input} />
                  <button disabled={busy || !reply.trim()} onClick={sendHumanReply} style={action}>ارسال انسانی</button>
                </div>
              </div>
            )}
          </section>
        </div>

        <section style={{ ...card, padding: 14, marginTop: 16 }}><b>Runtime Log</b><p style={{ marginBottom: 0, opacity: .7 }}>{log}</p></section>
      </section>
    </main>
  );
}
