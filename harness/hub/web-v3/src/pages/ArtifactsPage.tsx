import { useMemo, useState } from 'react'
import { artifactSummary, isArtifact } from '../lib/artifact'
import { Button, Chip, Input, ProviderDot } from '../lib/ui'
import { Markdown } from '../lib/markdown'

type Message = { role: string; content: string; streaming?: boolean }
type Chat = { id: string; title: string; provider: string; messages?: Message[] }
type ArtifactItem = { key: string; chat: Chat; message: Message; index: number }

const loadArtifacts = (): ArtifactItem[] => {
  try {
    const chats = JSON.parse(localStorage.getItem('hub-v3-chats') ?? '[]') as Chat[]
    return (Array.isArray(chats) ? chats : []).flatMap(chat => (chat.messages ?? []).flatMap((message, index) => isArtifact(message) ? [{ key: `${chat.id}:${index}`, chat, message, index }] : []))
  } catch { return [] }
}

export default function ArtifactsPage() {
  const [items] = useState(loadArtifacts); const [query, setQuery] = useState(''); const [selectedKey, setSelectedKey] = useState(items[0]?.key ?? ''); const [tab, setTab] = useState<'Output' | 'Review Issues' | 'References' | 'Versions'>('Output')
  const filtered = useMemo(() => items.filter(item => `${artifactSummary(item.message.content).title} ${item.chat.title}`.toLowerCase().includes(query.toLowerCase())), [items, query])
  const selected = items.find(item => item.key === selectedKey) ?? filtered[0]
  const select = (item: ArtifactItem) => setSelectedKey(item.key)
  const editInChat = () => { if (!selected) return; sessionStorage.setItem('hub-v3-active-chat', selected.chat.id); window.location.hash = '#/chat' }
  const empty = <div className="rounded-lg border border-dashed border-border-subtle px-space-4 py-space-8 text-center"><div className="text-label font-semibold text-primary">Chưa có dữ liệu</div><p className="mt-space-1 text-caption text-muted">Chưa có phiên bản hoặc dữ liệu backend cho mục này. Versioning artifact chưa nối backend — TODO(backend).</p></div>
  return <div className="flex h-full min-h-0 flex-col gap-space-4 p-space-6">
    <div className="flex flex-wrap items-end justify-between gap-space-3"><div><div className="mb-space-1 text-section font-semibold uppercase tracking-section text-muted">ĐIỀU PHỐI</div><h1 className="text-title font-semibold text-primary">Artifacts</h1><p className="mt-space-1 text-caption text-secondary">Output thật từ các assistant message đủ điều kiện trong chat.</p></div><Button variant="secondary" onClick={editInChat} disabled={!selected}>Edit in Chat</Button></div>
    <div className="flex min-h-0 flex-1 gap-space-4 overflow-hidden">
      <aside className="flex w-[280px] shrink-0 flex-col overflow-hidden rounded-lg border border-border-subtle bg-surface"><div className="border-b border-border-subtle p-space-3"><Input value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm artifact…" aria-label="Tìm artifact" /></div><div className="min-h-0 flex-1 overflow-y-auto p-space-2">{filtered.length === 0 ? <p className="p-space-3 text-caption text-muted">Chưa có artifact nào.</p> : filtered.map(item => { const summary = artifactSummary(item.message.content); return <button key={item.key} onClick={() => select(item)} className={`mb-space-1 block w-full rounded-md p-space-3 text-left ${item.key === selected?.key ? 'bg-accent-subtle' : 'hover:bg-hover'}`}><div className="flex items-center gap-space-2"><span className="flex h-7 w-7 items-center justify-center rounded-md bg-elevated text-accent">▤</span><span className="min-w-0 flex-1 truncate text-label font-semibold text-primary">{summary.title}</span></div><div className="mt-space-2 flex items-center gap-space-2 text-caption text-muted"><ProviderDot provider={item.chat.provider as 'claude' | 'codex' | 'nvidia' | 'gemini'} />{item.chat.title}<span>· {summary.chars} ký tự</span></div></button> })}</div></aside>
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-border-subtle bg-surface"><div className="flex flex-wrap items-center gap-space-2 border-b border-border-subtle p-space-3">{(['Output', 'Review Issues', 'References', 'Versions'] as const).map(name => <button key={name} onClick={() => setTab(name)} className={`rounded-md px-space-3 py-space-2 text-label ${tab === name ? 'bg-accent-subtle font-semibold text-primary' : 'text-secondary hover:bg-hover'}`}>{name}{name !== 'Output' && ' (0)'}</button>)}</div>{selected ? <><div className="border-b border-border-subtle p-space-5"><div className="flex items-start justify-between gap-space-4"><div><h2 className="text-title font-semibold text-primary">{artifactSummary(selected.message.content).title}</h2><div className="mt-space-2 flex items-center gap-space-2 text-caption text-secondary"><ProviderDot provider={selected.chat.provider as 'claude' | 'codex' | 'nvidia' | 'gemini'} />{selected.chat.title}</div></div><Chip>v1 · hiện tại</Chip></div><div className="mt-space-4 grid grid-cols-2 gap-space-3 text-caption md:grid-cols-3">{['Workflow name', 'Run ID', 'Được tạo bởi', 'Bắt đầu lúc', 'Hoàn thành lúc', 'Thời gian chạy'].map(label => <div key={label}><div className="text-muted">{label}</div><div className="mt-1 text-secondary">—</div></div>)}</div></div><div className="min-h-0 flex-1 overflow-y-auto p-space-5">{tab === 'Output' ? <div className="artifact-panel text-label"><Markdown source={selected.message.content} /></div> : empty}</div></> : <div className="flex flex-1 items-center justify-center p-space-6"><div className="max-w-md text-center"><div className="text-label font-semibold text-primary">Chưa có artifact nào</div><p className="mt-space-1 text-caption text-muted">Artifact sẽ xuất hiện sau khi AI tạo output đủ điều kiện trong chat.</p></div></div>}</main>
    </div>
  </div>
}
