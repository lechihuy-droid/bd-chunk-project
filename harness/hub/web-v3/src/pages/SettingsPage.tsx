import { useEffect, useState } from 'react'
import { ApiError, api } from '../lib/api'
import { Chip, ProviderDot, Status } from '../lib/ui'

type Provider = { id: string; available: boolean; version?: string | null; detail?: string }
type Catalog = { id?: string; shortName?: string; label?: string; category?: string }
type Models = { models?: string[]; default?: string; catalog?: Catalog[] }
type Health = { root?: string; runs_dir?: string; port?: number }
const provider = (id: string) => ['claude', 'codex', 'nvidia', 'gemini'].includes(id) ? id as 'claude' | 'codex' | 'nvidia' | 'gemini' : 'nvidia'

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]); const [models, setModels] = useState<Models>({}); const [health, setHealth] = useState<Health>({}); const [error, setError] = useState('')
  useEffect(() => { void Promise.all([api<Provider[]>('/api/providers'), api<Models>('/api/chat/models'), api<Health>('/api/health')]).then(([p, m, h]) => { setProviders(p); setModels(m); setHealth(h) }).catch(e => setError(e instanceof ApiError ? e.message : 'Không thể tải cài đặt')) }, [])
  const catalog: Catalog[] = models.catalog ?? (models.models ?? []).map(id => ({ id }))
  return <div className="flex h-full min-h-0 flex-col gap-4 overflow-auto p-7"><header><div className="mb-2 text-[length:var(--hub-section-size)] font-semibold uppercase tracking-[var(--hub-section-tracking)] text-muted">HỆ THỐNG</div><h1 className="text-[length:var(--hub-title-size)] font-semibold">Cài đặt</h1><p className="text-secondary">Thông tin hệ thống chỉ đọc.</p></header>{error && <div className="text-xs text-error">{error}</div>}<section><h2 className="mb-2 text-xs font-semibold">Sức khỏe provider</h2><div className="grid gap-3 md:grid-cols-2">{providers.map(item => <article key={item.id} className="rounded-[var(--hub-radius-lg)] border border-border-subtle bg-surface p-4"><div className="flex items-center gap-2"><ProviderDot provider={provider(item.id)} /><span className="font-mono text-sm">{item.id}</span><Status kind={item.available ? 'ready' : 'error'} label={item.available ? 'OK' : 'ERR'} className="ml-auto" /></div><dl className="mt-3 space-y-1 text-xs"><div className="flex justify-between gap-3"><dt className="text-muted">Version</dt><dd className="font-mono text-secondary">{item.version ?? '—'}</dd></div><div className="flex justify-between gap-3"><dt className="text-muted">Chi tiết</dt><dd className="text-right text-secondary">{item.detail || '—'}</dd></div></dl></article>)}</div></section><section><h2 className="mb-2 text-xs font-semibold">Model catalog</h2><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{catalog.map((model, index) => <div key={model.id ?? index} className="rounded-[var(--hub-radius-md)] border border-border-subtle bg-surface px-3 py-2 text-xs"><div className="flex items-center gap-2"><span className="font-mono text-primary">{model.shortName ?? model.label ?? model.id}</span>{model.id === models.default && <Chip>default</Chip>}</div><div className="mt-1 text-[10px] text-muted">{model.category ?? 'Model'} · {model.id}</div></div>)}</div></section><section className="rounded-[var(--hub-radius-lg)] border border-border-subtle bg-surface p-4"><h2 className="mb-3 text-xs font-semibold">Hệ thống</h2><dl className="grid gap-2 text-xs md:grid-cols-3"><Info label="Root" value={health.root} /><Info label="Runs dir" value={health.runs_dir} /><Info label="Port" value={health.port} /></dl></section></div>
}
function Info({ label, value }: { label: string; value?: string | number }) { return <div><dt className="text-muted">{label}</dt><dd className="mt-1 break-all font-mono text-[11px] text-secondary">{value ?? '—'}</dd></div> }


