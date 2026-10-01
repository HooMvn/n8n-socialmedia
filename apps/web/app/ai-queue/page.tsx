'use client';

import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type Draft = {
  id: string;
  conversation_id: string;
  source_message_id: string;
  intent: string;
  confidence: number;
  model: string;
  body: string;
  status: string;
  created_at: string;
};

type Evidence = {
  chunk_id: string;
  source_id: string;
  title: string;
  body: string;
  rank: number;
  score: number;
};

const input: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', padding: '12px 14px', borderRadius: 12,
  border: '1px solid rgba(15,23,42,.15)', font: 'inherit', marginTop: 6,
};
const button: React.CSSProperties = {
  border: 0, borderRadius: 12, padding: '10px 14px', background: '#174A3A', color: '#fff', cursor: 'pointer', font: 'inherit',
};

export default function AIQueuePage() {
  const [workspaceId, setWorkspaceId] = useState('');
  const [token, setToken] = useState('');
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [status, setStatus] = useState('Workspace و Access Token را وارد کنید.');

  useEffect(() => {
    setWorkspaceId(localStorage.getItem('engage_workspace_id') ?? '');
    setToken(localStorage.getItem('engage_token') ?? '');
  }, []);

  async function api<T>(path: string, init?: RequestInit): Promise<T> {
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

  async function load() {
    try {
      localStorage.setItem('engage_workspace_id', workspaceId);
      localStorage.setItem('engage_token', token);
      const data = await api<Draft[]>(`/api/v1/workspaces/${workspaceId}/ai/drafts`);
      setDrafts(data);
      setStatus(`${data.length} Draft منتظر Review است.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'خطای ناشناخته');
    }
  }

  async function review(draft: Draft, decision: 'approved' | 'rejected', editedBody?: string) {
    try {
      await api(`/api/v1/workspaces/${workspaceId}/ai/drafts/${draft.id}/review`, {
        method: 'POST',
        body: JSON.stringify({ decision, note: 'Reviewed from AI Queue', edited_body: editedBody ?? null }),
      });
      setDrafts(current => current.filter(item => item.id !== draft.id));
      setStatus(decision === 'approved' ? 'Draft تأیید شد و Outbound Message در صف قرار گرفت.' : 'Draft رد شد.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'خطای ناشناخته');
    }
  }

  async function loadEvidence(draftId: string): Promise<Evidence[]> {
    return api<Evidence[]>(`/api/v1/workspaces/${workspaceId}/ai/drafts/${draftId}/evidence`);
  }

  return (
    <main dir="rtl" style={{ minHeight: '100vh', padding: '32px 18px 72px', background: '#f5f7f6', color: '#10231d', fontFamily: 'system-ui,sans-serif' }}>
      <section style={{ maxWidth: 1080, margin: '0 auto' }}>
        <a href="/" style={{ color: '#174A3A', textDecoration: 'none' }}>← Risheh Engage</a>
        <p style={{ opacity: .55, marginBottom: 6 }}>v0.7 · Grounded AI + Human-in-the-loop</p>
        <h1 style={{ fontSize: 'clamp(32px,5vw,56px)', margin: 0 }}>AI Reply Review Queue</h1>
        <p style={{ lineHeight: 1.9, opacity: .7, maxWidth: 800 }}>
          Reviewer علاوه بر متن Draft می‌تواند Evidence بازیابی‌شده را ببیند. نبود Evidence برای Grounded Draft باید باعث توقف و Human Review شود.
        </p>

        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 12, marginBottom: 22 }}>
          <label>Workspace ID<input value={workspaceId} onChange={e => setWorkspaceId(e.target.value)} style={input} /></label>
          <label>Access Token<input value={token} onChange={e => setToken(e.target.value)} style={input} type="password" /></label>
        </section>
        <button onClick={load} style={button}>بارگذاری صف Review</button>
        <p style={{ opacity: .7 }}>{status}</p>

        <div style={{ display: 'grid', gap: 14 }}>
          {drafts.map(draft => <DraftCard key={draft.id} draft={draft} onReview={review} loadEvidence={loadEvidence} />)}
          {!drafts.length && <div style={{ padding: 28, borderRadius: 18, background: '#fff', border: '1px solid rgba(15,23,42,.08)' }}>Draft منتظر بررسی وجود ندارد.</div>}
        </div>
      </section>
    </main>
  );
}

function DraftCard({ draft, onReview, loadEvidence }: { draft: Draft; onReview: (draft: Draft, decision: 'approved' | 'rejected', editedBody?: string) => Promise<void>; loadEvidence: (draftId: string) => Promise<Evidence[]> }) {
  const [body, setBody] = useState(draft.body);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [evidenceStatus, setEvidenceStatus] = useState('');

  async function inspectEvidence() {
    try {
      const items = await loadEvidence(draft.id);
      setEvidence(items);
      setEvidenceStatus(items.length ? `${items.length} Evidence پیدا شد.` : 'این Draft Evidence ثبت‌شده ندارد.');
    } catch (error) {
      setEvidenceStatus(error instanceof Error ? error.message : 'خطا در Evidence');
    }
  }

  return (
    <article style={{ padding: 20, borderRadius: 20, background: '#fff', border: '1px solid rgba(15,23,42,.1)', boxShadow: '0 14px 40px rgba(15,23,42,.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <strong>{draft.intent}</strong>
        <span>{draft.confidence}% · {draft.model}</span>
      </div>
      <textarea value={body} onChange={e => setBody(e.target.value)} style={{ ...input, minHeight: 140, lineHeight: 1.9 }} />
      <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
        <button onClick={() => onReview(draft, 'approved', body)} style={button}>تأیید و ارسال</button>
        <button onClick={() => onReview(draft, 'rejected')} style={{ ...button, background: '#7f1d1d' }}>رد Draft</button>
        <button onClick={inspectEvidence} style={{ ...button, background: '#12304A' }}>مشاهده Evidence</button>
      </div>
      {evidenceStatus && <p style={{ opacity: .65 }}>{evidenceStatus}</p>}
      {evidence.map(item => (
        <section key={item.chunk_id} style={{ marginTop: 10, padding: 12, borderRadius: 12, background: '#f5f7f6' }}>
          <b>#{item.rank} · {item.title} · score={item.score}</b>
          <p style={{ lineHeight: 1.8, marginBottom: 0 }}>{item.body}</p>
        </section>
      ))}
    </article>
  );
}
