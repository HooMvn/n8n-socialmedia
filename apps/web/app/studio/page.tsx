'use client';

import { FormEvent, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type StepState = {
  workspaceId?: string;
  brandId?: string;
  contentId?: string;
  publicationId?: string;
  contentStatus?: string;
  publicationStatus?: string;
};

const card: React.CSSProperties = {
  border: '1px solid rgba(15,23,42,.12)', borderRadius: 20, padding: 20,
  background: 'rgba(255,255,255,.88)', boxShadow: '0 16px 48px rgba(15,23,42,.06)'
};
const input: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', padding: '12px 14px', borderRadius: 12,
  border: '1px solid rgba(15,23,42,.16)', marginTop: 6, font: 'inherit'
};
const button: React.CSSProperties = {
  border: 0, borderRadius: 12, padding: '11px 16px', background: '#174A3A',
  color: '#fff', cursor: 'pointer', font: 'inherit'
};

async function api<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
  return body as T;
}

export default function StudioPage() {
  const [token, setToken] = useState('');
  const [identity, setIdentity] = useState('');
  const [state, setState] = useState<StepState>({});
  const [log, setLog] = useState('ابتدا حساب Demo بسازید یا وارد شوید.');
  const [busy, setBusy] = useState(false);

  const canWorkspace = Boolean(token);
  const canBrand = Boolean(token && state.workspaceId);
  const canContent = Boolean(token && state.workspaceId && state.brandId);
  const canReview = Boolean(token && state.workspaceId && state.contentId);
  const canPublish = state.contentStatus === 'approved';

  const progress = useMemo(() => {
    const checks = [token, state.workspaceId, state.brandId, state.contentId, state.contentStatus === 'approved', state.publicationId];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [token, state]);

  async function run(action: () => Promise<void>) {
    try { setBusy(true); await action(); }
    catch (error) { setLog(error instanceof Error ? `خطا: ${error.message}` : 'خطای ناشناخته'); }
    finally { setBusy(false); }
  }

  function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const mode = String(data.get('mode'));
    void run(async () => {
      const payload = mode === 'register'
        ? { email: data.get('email'), password: data.get('password'), full_name: data.get('full_name') }
        : { email: data.get('email'), password: data.get('password') };
      const result = await api<{ access_token: string }>(`/api/v1/auth/${mode}`, undefined, {
        method: 'POST', body: JSON.stringify(payload),
      });
      setToken(result.access_token);
      const me = await api<{ email: string; full_name: string }>('/api/v1/auth/me', result.access_token);
      setIdentity(`${me.full_name} · ${me.email}`);
      setLog('احراز هویت موفق است. حالا Workspace بسازید.');
    });
  }

  function createWorkspace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void run(async () => {
      const result = await api<{ id: string }>('/api/v1/workspaces', token, {
        method: 'POST', body: JSON.stringify({ name: data.get('name'), slug: data.get('slug') }),
      });
      setState({ workspaceId: result.id });
      setLog(`Workspace ساخته شد و کاربر جاری Owner است: ${result.id}`);
    });
  }

  function saveBrand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!state.workspaceId) return;
    const data = new FormData(event.currentTarget);
    void run(async () => {
      const result = await api<{ id: string }>(`/api/v1/workspaces/${state.workspaceId}/brand`, token, {
        method: 'PUT', body: JSON.stringify({ name: data.get('name'), tone_of_voice: data.get('tone'), audience: data.get('audience'), forbidden_terms: data.get('forbidden') }),
      });
      setState((current) => ({ ...current, brandId: result.id }));
      setLog('Brand Brain پایه ذخیره شد.');
    });
  }

  function createContent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!state.workspaceId || !state.brandId) return;
    const data = new FormData(event.currentTarget);
    void run(async () => {
      const result = await api<{ id: string; status: string }>(`/api/v1/workspaces/${state.workspaceId}/contents`, token, {
        method: 'POST', body: JSON.stringify({ brand_id: state.brandId, title: data.get('title'), body: data.get('body'), platform: data.get('platform') }),
      });
      setState((current) => ({ ...current, contentId: result.id, contentStatus: result.status }));
      setLog('Draft محتوا ساخته شد.');
    });
  }

  function action(name: 'submit-review' | 'approve' | 'publish') {
    if (!state.workspaceId || !state.contentId) return;
    void run(async () => {
      const isApprove = name === 'approve';
      const isPublish = name === 'publish';
      const result = await api<{ id?: string; status: string }>(
        `/api/v1/workspaces/${state.workspaceId}/contents/${state.contentId}/${name}`,
        token,
        {
          method: 'POST',
          body: JSON.stringify(isApprove
            ? { actor: identity || 'studio-user', note: 'Approved from authenticated Studio' }
            : isPublish ? { idempotency_key: `studio-${state.contentId}-${Date.now()}` } : {}),
        },
      );
      if (isPublish) {
        setState((current) => ({ ...current, publicationId: result.id, publicationStatus: result.status, contentStatus: 'publish_requested' }));
        setLog('Publication + Outbox Event ساخته شد؛ Worker آن را با تحویل مطمئن به n8n می‌فرستد.');
      } else {
        setState((current) => ({ ...current, contentStatus: result.status }));
        setLog(isApprove ? 'محتوا توسط کاربر مجاز تأیید شد.' : 'محتوا وارد Review شد.');
      }
    });
  }

  return (
    <main dir="rtl" style={{ minHeight: '100vh', padding: '32px 18px 72px', background: '#f5f7f6', fontFamily: 'system-ui,sans-serif', color: '#10231d' }}>
      <section style={{ maxWidth: 1120, margin: '0 auto' }}>
        <header style={{ marginBottom: 28 }}>
          <a href="/" style={{ color: '#174A3A', textDecoration: 'none' }}>← Risheh Engage</a>
          <p style={{ opacity: .55 }}>Vertical Slice 01 · Secure Studio · v0.4</p>
          <h1 style={{ margin: 0, fontSize: 'clamp(30px,5vw,56px)' }}>از هویت تا انتشار قابل اعتماد</h1>
          <p style={{ lineHeight: 1.9, opacity: .72 }}>Auth، RBAC، Approval و Outbox در این Demo واقعاً enforce می‌شوند.</p>
          <div style={{ height: 8, background: '#e1e8e5', borderRadius: 999, overflow: 'hidden' }}><div style={{ width: `${progress}%`, height: '100%', background: '#174A3A' }} /></div>
          <small>{progress}% مسیر تکمیل شده {identity ? `· ${identity}` : ''}</small>
        </header>

        <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))' }}>
          <form onSubmit={authenticate} style={card}>
            <strong>00 · Authentication</strong><p style={{ opacity: .65 }}>JWT + Argon2</p>
            <select name="mode" style={input}><option value="register">Register</option><option value="login">Login</option></select>
            <input name="full_name" defaultValue="Demo Owner" placeholder="نام" style={input} />
            <input name="email" type="email" defaultValue={`demo-${Date.now()}@example.com`} required style={input} />
            <input name="password" type="password" defaultValue="ChangeMe-12345" minLength={10} required style={input} />
            <button disabled={busy} style={{ ...button, marginTop: 14 }}>ورود / ثبت‌نام</button>
          </form>

          <form onSubmit={createWorkspace} style={{ ...card, opacity: canWorkspace ? 1 : .45 }}>
            <strong>01 · Workspace</strong><p style={{ opacity: .65 }}>مالکیت Tenant و Owner Membership.</p>
            <input name="name" defaultValue="Demo Brand" required style={input} disabled={!canWorkspace} />
            <input name="slug" defaultValue={`demo-${Date.now()}`} required style={input} disabled={!canWorkspace} />
            <button disabled={!canWorkspace || busy} style={{ ...button, marginTop: 14 }}>ساخت Workspace</button>
          </form>

          <form onSubmit={saveBrand} style={{ ...card, opacity: canBrand ? 1 : .45 }}>
            <strong>02 · Brand Brain</strong>
            <input name="name" defaultValue="Risheh Demo" required style={input} disabled={!canBrand} />
            <textarea name="tone" defaultValue="شفاف، حرفه‌ای و انسانی" style={input} disabled={!canBrand} />
            <textarea name="audience" defaultValue="کسب‌وکارهای خدماتی و فروشگاهی" style={input} disabled={!canBrand} />
            <textarea name="forbidden" defaultValue="ادعای تضمینی، اطلاعات ساختگی" style={input} disabled={!canBrand} />
            <button disabled={!canBrand || busy} style={{ ...button, marginTop: 14 }}>ذخیره Brand</button>
          </form>

          <form onSubmit={createContent} style={{ ...card, opacity: canContent ? 1 : .45 }}>
            <strong>03 · Content Draft</strong>
            <input name="title" defaultValue="معرفی محصول" required style={input} disabled={!canContent} />
            <textarea name="body" defaultValue="متن محتوای آماده بررسی انسانی." required style={{ ...input, minHeight: 110 }} disabled={!canContent} />
            <select name="platform" style={input} disabled={!canContent}><option value="telegram">Telegram</option><option value="instagram">Instagram</option></select>
            <button disabled={!canContent || busy} style={{ ...button, marginTop: 14 }}>ساخت Draft</button>
          </form>

          <section style={{ ...card, opacity: canReview ? 1 : .45 }}>
            <strong>04 · Review & Approval</strong><p>وضعیت: <b>{state.contentStatus ?? '—'}</b></p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={() => action('submit-review')} disabled={!canReview || state.contentStatus !== 'draft' || busy} style={button}>Review</button>
              <button onClick={() => action('approve')} disabled={state.contentStatus !== 'in_review' || busy} style={button}>Approve</button>
            </div>
          </section>

          <section style={{ ...card, opacity: canPublish ? 1 : .45 }}>
            <strong>05 · Reliable Publish</strong><p style={{ opacity: .65 }}>Publication → Outbox → Worker → n8n</p>
            <button onClick={() => action('publish')} disabled={!canPublish || busy} style={button}>Publish Request</button>
            <p>Publication: <b>{state.publicationStatus ?? '—'}</b></p>
          </section>

          <section style={card}><strong>Runtime Log</strong><p style={{ lineHeight: 1.8 }}>{log}</p><code style={{ display: 'block', direction: 'ltr', textAlign: 'left', whiteSpace: 'pre-wrap', fontSize: 12 }}>{JSON.stringify(state, null, 2)}</code></section>
        </div>
      </section>
    </main>
  );
}
