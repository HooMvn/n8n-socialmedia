'use client';

import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type Source = { id: string; name: string; source_type: string; source_uri: string; status: string; created_at: string };

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(init?.headers ?? {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
  return body as T;
}

export default function KnowledgePage() {
  const [token, setToken] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [name, setName] = useState('FAQ اصلی');
  const [text, setText] = useState('');
  const [sources, setSources] = useState<Source[]>([]);
  const [log, setLog] = useState('Knowledge Source بسازید تا Grounded AI Evidence داشته باشد.');

  async function load() {
    try {
      const data = await request<Source[]>(`/api/v1/workspaces/${workspaceId}/knowledge/sources`, token);
      setSources(data); setLog(`${data.length} منبع دریافت شد.`);
    } catch (e) { setLog(e instanceof Error ? e.message : 'خطا'); }
  }

  async function create() {
    try {
      await request(`/api/v1/workspaces/${workspaceId}/knowledge/sources`, token, {
        method: 'POST',
        body: JSON.stringify({ name, source_type: 'faq', source_uri: '', text }),
      });
      setText(''); setLog('منبع ساخته و Chunk شد.'); await load();
    } catch (e) { setLog(e instanceof Error ? e.message : 'خطا'); }
  }

  const input: React.CSSProperties = { width: '100%', boxSizing: 'border-box', padding: 12, borderRadius: 12, border: '1px solid rgba(15,23,42,.15)', font: 'inherit' };
  return (
    <main dir="rtl" style={{ minHeight: '100vh', background: '#f5f7f6', color: '#10231d', padding: '28px 16px 64px', fontFamily: 'system-ui,sans-serif' }}>
      <section style={{ maxWidth: 980, margin: '0 auto' }}>
        <a href="/" style={{ color: '#174A3A', textDecoration: 'none' }}>← Risheh Engage</a>
        <p style={{ opacity: .55 }}>v0.7 · Grounded AI</p>
        <h1 style={{ fontSize: 'clamp(32px,5vw,56px)', marginBottom: 8 }}>Knowledge Sources</h1>
        <p style={{ opacity: .7, lineHeight: 1.8 }}>FAQ، Policy و دانش محصول را ثبت کنید؛ Backend آن را Chunk می‌کند و Grounded Draft فقط از Evidence مرتبط استفاده می‌کند.</p>

        <section style={{ background: '#fff', borderRadius: 20, padding: 18, border: '1px solid rgba(15,23,42,.1)', display: 'grid', gap: 12 }}>
          <label>JWT Token<textarea value={token} onChange={e => setToken(e.target.value)} style={{ ...input, minHeight: 70, direction: 'ltr' }} /></label>
          <label>Workspace ID<input value={workspaceId} onChange={e => setWorkspaceId(e.target.value)} style={{ ...input, direction: 'ltr' }} /></label>
          <label>نام منبع<input value={name} onChange={e => setName(e.target.value)} style={input} /></label>
          <label>متن منبع<textarea value={text} onChange={e => setText(e.target.value)} style={{ ...input, minHeight: 170 }} /></label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={create} disabled={!token || !workspaceId || !text}>ثبت و Chunk</button>
            <button onClick={load} disabled={!token || !workspaceId}>بارگذاری منابع</button>
          </div>
        </section>

        <section style={{ marginTop: 16, display: 'grid', gap: 10 }}>
          {sources.map(source => <article key={source.id} style={{ background: '#fff', padding: 15, borderRadius: 16, border: '1px solid rgba(15,23,42,.08)' }}><b>{source.name}</b><div style={{ opacity: .6 }}>{source.source_type} · {source.status}</div></article>)}
        </section>
        <p style={{ marginTop: 16, opacity: .65 }}>{log}</p>
      </section>
    </main>
  );
}
