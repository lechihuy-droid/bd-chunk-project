import { FileText, Paperclip, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { Button, Chip, Input, Popover } from '../lib/ui'

export type RunInput = { kind: 'artifact'; id: string } | { kind: 'chat_file'; chat_id: string; name: string }
type Artifact = { id: string; title: string }
type ChatFile = { chat_id: string; name: string }
type Copy = { add: string; artifacts: string; files: string; search: string; noArtifacts: string; noFiles: string; artifact: string; file: string; remove: string }

const keyFor = (item: RunInput) => item.kind === 'artifact' ? `artifact:${item.id}` : `chat_file:${item.chat_id}:${item.name}`

export default function RunInputPicker({ value, onChange, copy }: { value: RunInput[]; onChange: (value: RunInput[]) => void; copy: Copy }) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [files, setFiles] = useState<ChatFile[]>([])
  const [query, setQuery] = useState('')
  useEffect(() => { void Promise.all([api<{ artifacts: Artifact[] }>('/api/artifacts'), api<ChatFile[]>('/api/chat-files')]).then(([artifactData, fileData]) => { setArtifacts(artifactData.artifacts); setFiles(fileData) }).catch(() => { setArtifacts([]); setFiles([]) }) }, [])
  const selected = new Set(value.map(keyFor)); const needle = query.trim().toLowerCase()
  const shownArtifacts = useMemo(() => artifacts.filter(item => !needle || item.title.toLowerCase().includes(needle)), [artifacts, needle])
  const shownFiles = useMemo(() => files.filter(item => !needle || `${item.chat_id} ${item.name}`.toLowerCase().includes(needle)), [files, needle])
  const toggle = (item: RunInput) => onChange(selected.has(keyFor(item)) ? value.filter(existing => keyFor(existing) !== keyFor(item)) : [...value, item])
  const name = (item: RunInput) => item.kind === 'artifact' ? artifacts.find(row => row.id === item.id)?.title ?? item.id : item.name
  return <div className="flex flex-wrap items-center gap-space-2"><Popover label={<><Paperclip size={16} strokeWidth={1.75} aria-hidden="true" />{copy.add}</>} aria-label={copy.add} className="w-[320px] max-h-[420px] overflow-y-auto"><div className="space-y-space-3"><Input value={query} onChange={event => setQuery(event.target.value)} placeholder={copy.search} aria-label={copy.search} /><PickerSection title={copy.artifacts} empty={copy.noArtifacts}>{shownArtifacts.map(item => { const input: RunInput = { kind: 'artifact', id: item.id }; return <PickerRow key={item.id} label={item.title} selected={selected.has(keyFor(input))} onClick={() => toggle(input)} /> })}</PickerSection><PickerSection title={copy.files} empty={copy.noFiles}>{shownFiles.map(item => { const input: RunInput = { kind: 'chat_file', chat_id: item.chat_id, name: item.name }; return <PickerRow key={`${item.chat_id}/${item.name}`} label={`${item.name} · ${item.chat_id}`} selected={selected.has(keyFor(input))} onClick={() => toggle(input)} /> })}</PickerSection></div></Popover>{value.map(item => <Chip key={keyFor(item)} onRemove={() => onChange(value.filter(existing => keyFor(existing) !== keyFor(item)))} removeLabel={copy.remove}><FileText size={14} strokeWidth={1.75} aria-hidden="true" />{name(item)} · {item.kind === 'artifact' ? copy.artifact : copy.file}</Chip>)}</div>
}

function PickerSection({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) { const rows = Array.isArray(children) ? children : [children]; return <section><div className="mb-space-1 text-section font-semibold uppercase tracking-section text-muted">{title}</div>{rows.length ? <div className="space-y-1">{rows}</div> : <p className="text-caption text-muted">{empty}</p>}</section> }
function PickerRow({ label, selected, onClick }: { label: string; selected: boolean; onClick: () => void }) { return <Button type="button" variant={selected ? 'secondary' : 'ghost'} size="sm" onClick={onClick} className="w-full justify-start truncate"><span className="truncate">{label}</span>{selected && <X className="ml-auto" size={14} strokeWidth={1.75} aria-hidden="true" />}</Button> }
