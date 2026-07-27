import { useEffect, useMemo, useRef, useState } from 'react'
import { api, apiRequest } from '../lib/api'
import { parseSse } from '../lib/sse'
import { Markdown } from '../lib/markdown'
import { artifactSummary, isArtifact } from '../lib/artifact'
import { Button, Chip, IconButton, Popover, ProviderDot, Textarea } from '../lib/ui'

// ── AI Chat Workspace ─────────────────────────────────────────────────────────
// Three-panel workspace (imported from the "AI Workspace" design system, mapped to
// the hub token set): top bar · sidebar (Chats/Files/Artifacts) · chat · artifact.
// A single active chat is the primary shape; the model picker, context, artifact
// panel, version history and export all hang off it. Chat, models, providers,
// agents and skills are wired to the real backend; Files, artifact versioning and
// PDF/share export have no backend yet and are marked TODO(backend).

type Provider = { id: string; available: boolean; version?: string; detail: string; capabilities?: { stream?: boolean; resume?: boolean; models?: number } }
type Catalog = { id: string; shortName?: string; category?: string; label?: string }
type Skill = { id: string; name?: string; title?: string; description?: string }
type ActiveSkill = { id: string; scope: 'turn' | 'window' }
type Message = { role: 'user' | 'assistant' | 'system'; content: string; reasoning?: string; usage?: Record<string, unknown>; streaming?: boolean }
type Chat = { id: string; title: string; provider: string; model: string; agentId?: string; cliSessionId?: string; messages: Message[]; notice?: string; updatedAt: number }
type PinnedMessage = { id: string; content: string }
type Instruction = { id: string; label: string; active: boolean }
type SharedContextState = { text: string; pinned: PinnedMessage[]; instructions: Instruction[] }

const chatsKey = 'hub-v3-chats'
const sharedContextKey = 'hub-v3-shared-context'
const providerKinds = ['claude', 'codex', 'nvidia', 'gemini'] as const
type ProviderKind = (typeof providerKinds)[number]
const asKind = (id: string): ProviderKind => (providerKinds as readonly string[]).includes(id) ? id as ProviderKind : 'nvidia'

// Honest, provider-level capability copy — no fabricated per-model speed/cost ratings.
const providerRole: Record<string, { role: string; note: string }> = {
  claude: { role: 'CLI code · tools · artifacts', note: 'Cần Claude Code CLI cài sẵn' },
  codex: { role: 'CLI code · refactor', note: 'Chạy qua Codex CLI' },
  nvidia: { role: 'API chat · chọn model cụ thể', note: 'Nhanh, rẻ; không có tool' },
  gemini: { role: 'CLI đa phương thức', note: 'Chưa cài trên máy này' },
}

const formatTokens = (value: number) => value < 1000 ? String(value) : value < 1e6 ? `${(value / 1000).toFixed(1).replace(/\.0$/, '')}k` : `${(value / 1e6).toFixed(1).replace(/\.0$/, '')}M`
const estimateTokens = (text: string) => Math.ceil(text.length / 4)

const defaultInstructions: Instruction[] = [{ id: 'i1', label: 'Giữ giọng chuyên nghiệp, ngắn gọn', active: true }]
const loadSharedContext = (): SharedContextState => {
  try {
    const value = JSON.parse(localStorage.getItem(sharedContextKey) ?? 'null')
    return {
      text: typeof value?.text === 'string' ? value.text : '',
      pinned: Array.isArray(value?.pinned) ? value.pinned.filter((i: PinnedMessage) => typeof i?.id === 'string' && typeof i?.content === 'string').slice(0, 10) : [],
      instructions: Array.isArray(value?.instructions) && value.instructions.length ? value.instructions : defaultInstructions,
    }
  } catch { return { text: '', pinned: [], instructions: defaultInstructions } }
}
const activeInstructionText = (context: SharedContextState) => context.instructions.filter(i => i.active).map(i => i.label)
const sharedText = (context: SharedContextState) => [context.text.trim(), ...context.pinned.map(i => i.content.trim()), ...activeInstructionText(context)].filter(Boolean).join('\n\n')
const promptFor = (context: SharedContextState, text: string, inject: boolean, extra = '') => { const contextText = [sharedText(context), extra].filter(Boolean).join('\n\n'); return inject && contextText ? `[Bối cảnh chung]\n${contextText}\n\n[Yêu cầu]\n${text}` : text }

const providerState = (provider?: Provider) => {
  if (!provider?.available) {
    const detail = provider?.detail?.toLowerCase() ?? ''
    if (/not set|not configured|environment|api key|token/.test(detail)) return { label: 'chưa cấu hình', kind: 'setup-required' as const }
    if (detail === 'not_installed') return { label: 'chưa cài', kind: 'not-installed' as const }
    return { label: 'không khả dụng', kind: 'error' as const }
  }
  return { label: 'sẵn sàng', kind: 'ready' as const }
}

const makeChat = (provider = 'nvidia', model = ''): Chat => ({ id: crypto.randomUUID(), title: 'Trò chuyện mới', provider, model, messages: [], updatedAt: Date.now() })
const loadChats = (): Chat[] => { try { const v = JSON.parse(localStorage.getItem(chatsKey) ?? 'null'); return Array.isArray(v) && v.length ? v : [makeChat()] } catch { return [makeChat()] } }
const chatSubtitle = (chat: Chat) => { const last = [...chat.messages].reverse().find(m => m.content.trim()); return last ? last.content.replace(/\s+/g, ' ').slice(0, 42) : 'Chưa có tin nhắn' }
const modelShort = (chat: Chat, catalog: Catalog[]) => chat.model ? (catalog.find(m => m.id === chat.model)?.shortName ?? chat.model.split('/').at(-1) ?? chat.model) : 'theo CLI'
const activeChatHandoffKey = 'hub-v3-active-chat'

export default function ChatPage() {
  const [chats, setChats] = useState<Chat[]>(loadChats)
  const [activeChatId, setActiveChatId] = useState<string>(() => loadChats()[0].id)
  const [leftTab, setLeftTab] = useState<'chats' | 'files' | 'artifacts'>('chats')
  const [providers, setProviders] = useState<Provider[]>([])
  const [catalog, setCatalog] = useState<Catalog[]>([])
  const [defaultModel, setDefaultModel] = useState('')
  const [skills, setSkills] = useState<Skill[]>([])
  const [activeSkills, setActiveSkills] = useState<ActiveSkill[]>([])
  const [sharedContext, setSharedContext] = useState<SharedContextState>(loadSharedContext)
  const [injectedContext, setInjectedContext] = useState<Record<string, string>>({})
  const [promptText, setPromptText] = useState('')
  const [contextOpen, setContextOpen] = useState(false)
  const [activeArtifactIndex, setActiveArtifactIndex] = useState<number | null>(null)
  const [artifactContextEnabled, setArtifactContextEnabled] = useState(true)
  const [artifactFocus, setArtifactFocus] = useState(false)
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const [showExport, setShowExport] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const controllers = useRef(new Map<string, AbortController>())
  const toastTimer = useRef<number | undefined>(undefined)

  const activeChat = chats.find(c => c.id === activeChatId) ?? chats[0]
  const artifactMessages = useMemo(() => activeChat.messages.map((m, index) => ({ m, index })).filter(({ m }) => isArtifact(m)), [activeChat])
  const activeArtifact = activeArtifactIndex != null && isArtifact(activeChat.messages[activeArtifactIndex]) ? activeChat.messages[activeArtifactIndex] : null
  const isEmptyPhase = activeChat.messages.length === 0

  useEffect(() => { localStorage.setItem(chatsKey, JSON.stringify(chats.map(c => ({ ...c, messages: c.messages.map(({ streaming: _s, ...m }) => m) })))) }, [chats])
  useEffect(() => { localStorage.setItem(sharedContextKey, JSON.stringify(sharedContext)) }, [sharedContext])
  useEffect(() => { setActiveArtifactIndex(null) }, [activeChatId])
  useEffect(() => { const handoff = sessionStorage.getItem(activeChatHandoffKey); if (handoff && chats.some(chat => chat.id === handoff)) { setActiveChatId(handoff); sessionStorage.removeItem(activeChatHandoffKey) } }, [chats])
  useEffect(() => () => window.clearTimeout(toastTimer.current), [])
  useEffect(() => {
    void Promise.all([
      api<Provider[]>('/api/providers'),
      api<{ catalog: Catalog[]; default: string }>('/api/chat/models'),
      api<string[]>('/api/skills/names'),
    ]).then(([p, m, s]) => {
      setProviders(p); setCatalog(m.catalog); setDefaultModel(m.default); setSkills(s.map(id => ({ id })))
      setChats(current => current.map(c => c.provider === 'nvidia' && !c.model ? { ...c, model: m.default } : c))
    }).catch(() => undefined)
  }, [])

  const showToast = (text: string) => { setToast(text); window.clearTimeout(toastTimer.current); toastTimer.current = window.setTimeout(() => setToast(null), 2400) }
  const patch = (id: string, change: Partial<Chat>) => setChats(current => current.map(c => c.id === id ? { ...c, ...change, updatedAt: Date.now() } : c))
  const patchLast = (id: string, change: Partial<Message> | ((m: Message) => Partial<Message>)) => setChats(current => current.map(c => c.id === id ? { ...c, messages: c.messages.map((m, n) => n === c.messages.length - 1 ? { ...m, ...(typeof change === 'function' ? change(m) : change) } : m) } : c))

  const newChat = () => { const chat = makeChat(activeChat.provider, activeChat.provider === 'nvidia' ? (activeChat.model || defaultModel) : ''); setChats(current => [chat, ...current]); setActiveChatId(chat.id); setLeftTab('chats'); setPromptText('') }
  const selectChat = (id: string) => { setActiveChatId(id); setLeftTab('chats') }
  const chooseModel = (provider: string, model: string) => { patch(activeChatId, { provider, model, agentId: undefined, cliSessionId: undefined }); setInjectedContext(c => { const n = { ...c }; delete n[activeChatId]; return n }) }

  const skillName = (skill: Skill) => skill.name ?? skill.title ?? skill.id
  const activateSkill = (name: string) => { const skill = skills.find(s => skillName(s).toLowerCase() === name.toLowerCase()); if (!skill || activeSkills.some(s => s.id === skillName(skill))) return false; setActiveSkills(c => [...c, { id: skillName(skill), scope: 'turn' }]); return true }
  const removeSkill = (id: string) => setActiveSkills(c => c.filter(s => s.id !== id))
  const skillDraft = promptText.startsWith('#') ? promptText.slice(1).toLowerCase() : ''
  const skillMatches = skillDraft ? skills.filter(s => skillName(s).toLowerCase().includes(skillDraft)).slice(0, 8) : []
  const changePrompt = (value: string) => { const match = value.match(/^#([\w-]+)\s$/); if (match && activateSkill(match[1])) { setPromptText(''); return } setPromptText(value) }

  const send = async (text: string, selectedSkills = activeSkills) => {
    const trimmed = text.trim(); if (!trimmed) return
    const chat = chats.find(c => c.id === activeChatId); if (!chat) return
    const artifactContext = artifactContextEnabled && activeArtifact ? `[Artifact đang mở]\n${activeArtifact.content}` : ''
    const fingerprint = `${sharedContext.text}\n${sharedContext.pinned.map(i => i.id).join('|')}\n${activeInstructionText(sharedContext).join('|')}\n${artifactContext}`
    const shouldInject = Boolean(sharedText(sharedContext) || artifactContext) && (!chat.messages.some(m => m.role === 'user') || injectedContext[chat.id] !== fingerprint)
    const prompt = promptFor(sharedContext, trimmed, shouldInject, artifactContext)
    const title = chat.messages.length === 0 ? trimmed.replace(/\s+/g, ' ').slice(0, 40) : chat.title
    const user: Message = { role: 'user', content: prompt }
    const assistant: Message = { role: 'assistant', content: '', reasoning: '', streaming: true }
    const history = [...chat.messages, user]
    patch(chat.id, { messages: [...history, assistant], title })
    const controller = new AbortController(); controllers.current.set(chat.id, controller)
    const providerInfo = providers.find(p => p.id === chat.provider)
    if (providerInfo && !providerInfo.available) { patchLast(chat.id, { role: 'system', content: providerInfo.detail || 'Provider không khả dụng', streaming: false }); controllers.current.delete(chat.id); return }
    // NVIDIA gets full history; CLI providers resume with only the new message when a session exists.
    const messages = (chat.provider !== 'nvidia' && chat.cliSessionId ? [user] : history).filter(m => m.role !== 'system')
    try {
      const response = await apiRequest('/api/chat', { method: 'POST', body: JSON.stringify({ provider: chat.provider, model: chat.model || undefined, agent_id: chat.agentId, messages, session_id: chat.cliSessionId, skills: selectedSkills.map(s => s.id) }), signal: controller.signal })
      if (!response.body) throw new Error('Chat stream unavailable')
      for await (const item of parseSse(response.body)) {
        const data = item.data as Record<string, unknown>
        if (item.event === 'reasoning') patchLast(chat.id, cur => ({ reasoning: `${cur.reasoning ?? ''}${String(data.text ?? '')}`, streaming: true }))
        if (item.event === 'delta') patchLast(chat.id, cur => ({ content: `${cur.content}${String(data.text ?? '')}`, streaming: true }))
        if (item.event === 'done') {
          if (shouldInject) setInjectedContext(c => ({ ...c, [chat.id]: fingerprint }))
          patchLast(chat.id, { streaming: false, usage: data.usage as Record<string, unknown> })
          patch(chat.id, { cliSessionId: typeof data.session_id === 'string' ? data.session_id : chat.cliSessionId, model: typeof data.model === 'string' && chat.provider === 'nvidia' ? data.model : chat.model, notice: typeof data.skill_notice === 'string' ? data.skill_notice : chat.notice })
        }
        if (item.event === 'error') patchLast(chat.id, { role: 'system', content: String(data.message ?? 'Chat stream error'), streaming: false })
      }
    } catch (error) { if ((error as Error).name !== 'AbortError') patchLast(chat.id, { role: 'system', content: (error as Error).message, streaming: false }) }
    finally { patchLast(chat.id, { streaming: false }); controllers.current.delete(chat.id) }
  }
  const submitPrompt = () => { const text = promptText.trim(); if (!text) return; const selected = activeSkills; setPromptText(''); void send(text, selected); if (selected.some(s => s.scope === 'turn')) setActiveSkills(c => c.filter(s => s.scope !== 'turn')) }
  const stop = () => controllers.current.get(activeChatId)?.abort()
  const retry = () => { const prompt = [...activeChat.messages].reverse().find(m => m.role === 'user')?.content; if (prompt) void send(prompt) }
  const streaming = Boolean(activeChat.messages.at(-1)?.streaming)

  const pin = (index: number, content: string) => setSharedContext(cur => { if (cur.pinned.length >= 10) { showToast('Tối đa 10 tin ghim.'); return cur } const id = `${activeChatId}:${index}`; return cur.pinned.some(i => i.id === id) ? cur : { ...cur, pinned: [...cur.pinned, { id, content }] } })
  const unpin = (id: string) => setSharedContext(cur => ({ ...cur, pinned: cur.pinned.filter(i => i.id !== id) }))
  const pinnedIds = new Set(sharedContext.pinned.map(i => i.id))
  // Section-level "edit" is a real backend round-trip: it sends a scoped follow-up prompt.
  const editSection = (heading: string, action: string) => { void send(`${action} phần "${heading}" trong artifact vừa tạo. Chỉ trả lại phần đó.`); showToast(`${action} · ${heading}`) }

  const contextEstimate = estimateTokens([sharedText(sharedContext), artifactContextEnabled && activeArtifact?.content].filter(Boolean).join('\n\n'))
  const contextTooLarge = contextEstimate > 8000
  const contextSummary = `Bối cảnh ~${formatTokens(contextEstimate)} token · Ghim ${sharedContext.pinned.length}/10`

  return <div className="chat-workspace">
    <TopBar workspace="Harness Hub" chat={activeChat} catalog={catalog} providers={providers} defaultModel={defaultModel}
      onChooseModel={chooseModel} exportDisabled={!activeArtifact} onExport={() => setShowExport(true)} onSettings={() => { window.location.hash = '#/settings' }} onToast={showToast} />
    <div className={`cw-body ${artifactFocus ? 'artifact-focus' : ''}`}>
      <WorkspaceSidebar tab={leftTab} onTab={setLeftTab} chats={chats} activeChatId={activeChatId} onNewChat={newChat} onSelectChat={selectChat}
        artifacts={artifactMessages} activeArtifactIndex={activeArtifactIndex} onSelectArtifact={i => setActiveArtifactIndex(i)} onUploadFile={() => showToast('Tải file: backend chưa nối')} />

      <div className="cw-center">
        {/* Context bar only once a conversation exists; the composer is always present. */}
        {!isEmptyPhase && <div className="flex items-center gap-space-2 border-b border-border-subtle px-space-4 py-space-2 text-caption text-secondary">
          <span className="min-w-0 truncate">{contextSummary}</span>{activeArtifact && <button onClick={() => setArtifactContextEnabled(v => !v)} className={`shrink-0 rounded-full border px-space-2 py-[3px] ${artifactContextEnabled ? 'border-accent bg-accent-subtle text-accent' : 'border-border-subtle text-muted'}`}>Bối cảnh: {artifactSummary(activeArtifact.content).title} · {activeChat.title}</button>}
          <Button variant="ghost" size="sm" className="shrink-0" onClick={() => setContextOpen(true)}>Quản lý</Button>
        </div>}
        <div className="cw-msgs">
          {isEmptyPhase
            ? <EmptyState onCreate={() => void send('Tạo một kế hoạch ra mắt sản phẩm')} suggestions={skills.slice(0, 6).map(skillName)} onSuggestion={label => void send(label)} />
            : <div className="space-y-space-4 p-space-4">
              {activeChat.notice && <p className="text-caption text-muted">{activeChat.notice}</p>}
              {activeChat.messages.map((m, i) => <MessageView key={i} message={m} last={i === activeChat.messages.length - 1}
                onOpenArtifact={() => { setActiveArtifactIndex(i); setLeftTab('artifacts') }} onRetry={retry} onCopy={() => { void navigator.clipboard?.writeText(m.content); showToast('Đã copy') }}
                pinned={pinnedIds.has(`${activeChatId}:${i}`)} onPin={() => pin(i, m.content)} onUnpin={() => unpin(`${activeChatId}:${i}`)} />)}
              {streaming && !activeChat.messages.at(-1)?.content && <ThinkingDots />}
            </div>}
        </div>
        {activeSkills.length > 0 && <div className="flex flex-wrap gap-space-2 px-space-4 pt-space-2">{activeSkills.map(skill => <Chip key={skill.id} onRemove={() => removeSkill(skill.id)}>#{skill.id}</Chip>)}</div>}
        {!isEmptyPhase && activeArtifact && <div className="flex flex-wrap gap-space-2 px-space-4 pt-space-2">{['Phân tích tài liệu', 'Tóm tắt', 'Rút gọn', 'Viết lại', 'Tạo slide', 'Hỏi về dữ liệu'].map(action => <button key={action} onClick={() => void send(`${action} tài liệu đang mở`)} className="shrink-0 whitespace-nowrap rounded-full border border-border-strong bg-surface px-space-3 py-[6px] text-caption text-secondary transition-colors hover:border-accent hover:text-accent">{action}</button>)}</div>}
        {!isEmptyPhase && skills.length > 0 && <div className="flex flex-wrap gap-space-2 px-space-4 pt-space-2">{skills.slice(0, 6).map(s => <button key={skillName(s)} onClick={() => activateSkill(skillName(s))} className="shrink-0 whitespace-nowrap rounded-full border border-border-strong bg-surface px-space-3 py-[6px] text-caption text-secondary transition-colors hover:border-accent hover:text-accent">#{skillName(s)}</button>)}</div>}
        <Composer value={promptText} onChange={changePrompt} onSubmit={submitPrompt} onStop={stop} streaming={streaming}
          placeholder={`Nhắn ${activeChat.provider}…`} skillMatches={skillMatches.map(skillName)} onPickSkill={name => { activateSkill(name); setPromptText('') }}
          onAttach={() => showToast('Đính kèm: backend chưa nối')} />
      </div>

      <div className="cw-artifact">
        {activeArtifact
          ? <ArtifactPanel message={activeArtifact} focused={artifactFocus} onFocus={() => setArtifactFocus(v => !v)} onPopout={() => showToast('Pop-out: chưa có route độc lập cho artifact — cần thêm sau')} onHistory={() => setShowVersionHistory(true)} onExport={() => setShowExport(true)} onCopy={() => { void navigator.clipboard?.writeText(activeArtifact.content); showToast('Đã copy') }} onEditSection={editSection} onSelection={(text, action) => { if (action === 'Copy') { void navigator.clipboard?.writeText(text); showToast('Đã copy vùng chọn'); return } if (action === 'Comment') { showToast('Comment: chưa nối backend'); return } void send(`${action} đoạn văn bản sau:\n"${text}"`) }} />
          : <ArtifactEmpty onOpenLibrary={() => setLeftTab('artifacts')} count={artifactMessages.length} />}
      </div>
    </div>

    {contextOpen && <ContextDrawer context={sharedContext} onChange={setSharedContext} tooLarge={contextTooLarge} estimate={contextEstimate} onClose={() => setContextOpen(false)} />}
    {showVersionHistory && activeArtifact && <VersionHistoryModal message={activeArtifact} onClose={() => setShowVersionHistory(false)} />}
    {showExport && activeArtifact && <ExportModal message={activeArtifact} onClose={() => setShowExport(false)} onToast={showToast} />}
    {toast && <div role="status" className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-full bg-elevated px-space-4 py-space-2 text-caption font-medium text-primary shadow-lg ring-1 ring-border-strong">{toast}</div>}
  </div>
}

// ── Top bar ───────────────────────────────────────────────────────────────────
function TopBar({ workspace, chat, catalog, providers, defaultModel, onChooseModel, exportDisabled, onExport, onSettings, onToast }: {
  workspace: string; chat: Chat; catalog: Catalog[]; providers: Provider[]; defaultModel: string
  onChooseModel: (provider: string, model: string) => void; exportDisabled: boolean; onExport: () => void; onSettings: () => void; onToast: (t: string) => void
}) {
  const label = `${chat.provider} · ${modelShort(chat, catalog)}`
  return <div className="flex h-full items-center justify-between gap-space-3 border-b border-border-subtle bg-sidebar px-space-4">
    <div className="flex min-w-0 items-center gap-space-2">
      <div className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-[7px] bg-accent text-[13px] font-bold text-app">W</div>
      <div className="truncate text-label font-semibold text-primary">{workspace}</div>
      <span className="flex shrink-0 items-center gap-[5px] rounded-full bg-[var(--color-success)]/15 px-[9px] py-[3px] text-caption font-semibold text-success"><span className="h-[6px] w-[6px] rounded-full bg-success" />Active</span>
    </div>
    <div className="flex shrink-0 items-center gap-space-2">
      <ModelSelector chat={chat} catalog={catalog} providers={providers} defaultModel={defaultModel} triggerLabel={label} onChoose={onChooseModel} />
      <div className="h-5 w-px bg-border-subtle" />
      <Button variant="secondary" size="sm" disabled={exportDisabled} onClick={onExport}>Export</Button>
      <IconButton icon="⚙" aria-label="Cài đặt" onClick={onSettings} />
      <button aria-label="Tài khoản" onClick={() => onToast('Tài khoản: chưa nối')} className="flex h-7 w-7 items-center justify-center rounded-full bg-elevated text-caption font-semibold text-secondary">U</button>
    </div>
  </div>
}

function ModelSelector({ chat, catalog, providers, defaultModel, triggerLabel, onChoose }: {
  chat: Chat; catalog: Catalog[]; providers: Provider[]; defaultModel: string; triggerLabel: string; onChoose: (provider: string, model: string) => void
}) {
  const grouped = useMemo(() => catalog.reduce<Record<string, Catalog[]>>((all, m) => { const key = m.category ?? 'Models'; (all[key] ??= []).push(m); return all }, {}), [catalog])
  const cards: Provider[] = providerKinds.map(id => providers.find(p => p.id === id) ?? { id, available: false, detail: 'không khả dụng' })
  return <Popover align="end" aria-label="Chọn model" triggerClassName="max-w-[260px]" className="w-[340px] max-h-[70vh] overflow-y-auto"
    label={<span className="flex min-w-0 items-center gap-[7px]"><span className="h-[7px] w-[7px] shrink-0 rounded-full bg-accent" /><span className="truncate text-label">{triggerLabel}</span><span className="shrink-0 text-caption text-muted">▾</span></span>}>
    {(close: () => void) => <div className="space-y-space-1">
      <div className="px-space-2 pb-space-1 text-section font-semibold uppercase tracking-section text-muted">Chọn model</div>
      {cards.map(p => {
        const state = providerState(p); const role = providerRole[p.id] ?? { role: '', note: '' }; const selected = chat.provider === p.id
        const caps = p.capabilities
        return <div key={p.id} className={`rounded-[9px] border p-space-3 ${selected ? 'border-accent bg-accent-subtle' : 'border-transparent'}`}>
          <button disabled={!p.available} onClick={() => { onChoose(p.id, p.id === 'nvidia' ? (chat.model || defaultModel) : ''); if (p.id !== 'nvidia') close() }}
            className="block w-full text-left disabled:cursor-not-allowed disabled:opacity-50">
            <div className="flex items-center justify-between gap-space-2">
              <span className="flex items-center gap-space-2 text-label font-semibold text-primary"><ProviderDot provider={asKind(p.id)} />{p.id}{selected && <span className="text-accent">✓</span>}</span>
              <span className={`text-caption ${state.kind === 'ready' ? 'text-success' : state.kind === 'error' ? 'text-error' : 'text-muted'}`}>{state.label}</span>
            </div>
            <div className="mt-[2px] text-caption text-secondary">{role.role}</div>
            <div className="mt-[2px] text-caption text-muted">{role.note}{p.version ? ` · ${p.version}` : ''}</div>
            {caps && <div className="mt-space-1 flex gap-space-3 text-caption text-muted">{caps.stream != null && <span>Stream: <b className="text-secondary">{caps.stream ? '✓' : '—'}</b></span>}{caps.resume != null && <span>Resume: <b className="text-secondary">{caps.resume ? '✓' : '—'}</b></span>}{caps.models != null && <span>Model: <b className="text-secondary">{caps.models}</b></span>}</div>}
          </button>
          {selected && p.id === 'nvidia' && <label className="mt-space-2 block space-y-space-1 text-caption text-muted">Model cụ thể
            <select value={chat.model || defaultModel} onChange={e => onChoose('nvidia', e.target.value)} className="h-input w-full rounded-md border border-border-subtle bg-elevated px-space-3 text-body text-primary">
              {Object.entries(grouped).map(([category, models]) => <optgroup key={category} label={category}>{models.map(m => <option key={m.id} value={m.id}>{m.shortName ?? m.label ?? m.id}</option>)}</optgroup>)}
            </select></label>}
        </div>
      })}
    </div>}
  </Popover>
}

// ── Left sidebar ────────────────────────────────────────────────────────────────
function WorkspaceSidebar({ tab, onTab, chats, activeChatId, onNewChat, onSelectChat, artifacts, activeArtifactIndex, onSelectArtifact, onUploadFile }: {
  tab: 'chats' | 'files' | 'artifacts'; onTab: (t: 'chats' | 'files' | 'artifacts') => void
  chats: Chat[]; activeChatId: string; onNewChat: () => void; onSelectChat: (id: string) => void
  artifacts: { m: Message; index: number }[]; activeArtifactIndex: number | null; onSelectArtifact: (i: number) => void; onUploadFile: () => void
}) {
  const tabs: { id: 'chats' | 'files' | 'artifacts'; icon: string; label: string; count: number }[] = [
    { id: 'chats', icon: '💬', label: 'Chats', count: chats.length },
    { id: 'files', icon: '📄', label: 'Files', count: 0 },
    { id: 'artifacts', icon: '▤', label: 'Artifacts', count: artifacts.length },
  ]
  return <div className="cw-sidebar">
    <div className="p-space-3 pb-space-2">
      <Button variant="secondary" onClick={onNewChat} className="w-full justify-center" icon={<span className="text-[15px] leading-none">+</span>}>Trò chuyện mới</Button>
    </div>
    <div className="flex flex-col gap-[2px] px-space-2">
      {tabs.map(t => <button key={t.id} onClick={() => onTab(t.id)} className={`flex items-center justify-between rounded-[7px] px-space-2 py-space-2 text-label ${tab === t.id ? 'bg-hover font-semibold text-primary' : 'text-secondary hover:bg-hover'}`}>
        <span className="flex items-center gap-space-2"><span>{t.icon}</span>{t.label}</span><span className="text-caption text-muted">{t.count}</span>
      </button>)}
    </div>
    <div className="min-h-0 flex-1 overflow-y-auto px-space-2 pb-space-3 pt-space-2">
      {tab === 'chats' && <>
        <SidebarHeading>Chats</SidebarHeading>
        {chats.map(c => <button key={c.id} onClick={() => onSelectChat(c.id)} className={`mb-[2px] block w-full rounded-md px-space-2 py-space-2 text-left ${c.id === activeChatId ? 'bg-hover' : 'hover:bg-hover'}`}>
          <div className={`truncate text-label ${c.id === activeChatId ? 'font-semibold text-primary' : 'text-primary'}`}>{c.title}</div>
          <div className="truncate text-caption text-muted">{chatSubtitle(c)}</div>
        </button>)}
      </>}
      {tab === 'files' && <>
        <div className="flex items-center justify-between px-space-1 pb-space-2 pt-space-1"><SidebarHeading inline>Files</SidebarHeading><button onClick={onUploadFile} className="text-caption font-semibold text-accent">+ Tải lên</button></div>
        <p className="px-space-1 py-space-2 text-caption text-muted">Chưa có file. <span className="text-tertiary">(backend chưa nối)</span></p>
      </>}
      {tab === 'artifacts' && <>
        <SidebarHeading>Artifacts</SidebarHeading>
        {artifacts.length === 0 && <p className="px-space-1 py-space-2 text-caption text-muted">Artifact do AI tạo sẽ hiện ở đây.</p>}
        {artifacts.map(({ m, index }) => { const s = artifactSummary(m.content); return <button key={index} onClick={() => onSelectArtifact(index)} className={`mb-[2px] block w-full rounded-md px-space-2 py-space-2 text-left ${index === activeArtifactIndex ? 'bg-hover' : 'hover:bg-hover'}`}>
          <div className="truncate text-label font-semibold text-primary">{s.title}</div>
          <div className="mt-[3px] flex items-center gap-space-2"><span className="rounded-full bg-accent-subtle px-space-2 py-[2px] text-caption font-semibold text-accent">Draft</span><span className="text-caption text-muted">{s.chars} ký tự</span></div>
        </button> })}
      </>}
    </div>
  </div>
}
function SidebarHeading({ children, inline }: { children: React.ReactNode; inline?: boolean }) {
  return <div className={`text-section font-semibold uppercase tracking-section text-muted ${inline ? '' : 'px-space-1 pb-space-2 pt-space-1'}`}>{children}</div>
}

// ── Center: empty state, messages, composer ────────────────────────────────────
function EmptyState({ onCreate, suggestions, onSuggestion }: { onCreate: () => void; suggestions: string[]; onSuggestion: (s: string) => void }) {
  return <div className="flex h-full flex-col items-center justify-center p-space-8">
    <div className="w-full max-w-[520px] text-center">
      <div className="mb-space-2 text-[22px] font-bold text-primary">Bạn muốn làm gì hôm nay?</div>
      <div className="mb-space-6 text-body text-secondary">Nhắn ở ô bên dưới, hoặc tạo artifact đầu tiên.</div>
      <div className="mb-space-6 flex justify-center"><Button variant="primary" onClick={onCreate}>Tạo Artifact</Button></div>
      {suggestions.length > 0 && <>
        <div className="mb-space-2 text-section font-semibold uppercase tracking-section text-muted">Gợi ý</div>
        <div className="flex flex-wrap justify-center gap-space-2">{suggestions.map(s => <button key={s} onClick={() => onSuggestion(s)} className="whitespace-nowrap rounded-full border border-border-strong bg-surface px-space-4 py-space-2 text-caption text-secondary transition-colors hover:border-accent hover:text-accent">{s}</button>)}</div>
      </>}
    </div>
  </div>
}

function ThinkingDots() {
  return <div className="flex justify-start"><div className="flex gap-[4px] rounded-[12px] bg-surface px-space-3 py-space-3">{[0, 0.2, 0.4].map(d => <span key={d} className="h-[6px] w-[6px] rounded-full bg-muted" style={{ animation: `run-pulse 1.2s infinite ease-in-out ${d}s` }} />)}</div></div>
}

function MessageView({ message, last, onOpenArtifact, onRetry, onCopy, pinned, onPin, onUnpin }: {
  message: Message; last: boolean; onOpenArtifact: () => void; onRetry: () => void; onCopy: () => void; pinned: boolean; onPin: () => void; onUnpin: () => void
}) {
  const [showReasoning, setShowReasoning] = useState(false)
  const artifact = isArtifact(message); const summary = artifact ? artifactSummary(message.content) : null
  if (message.role === 'system' && last) return <div className="rounded-[12px] border border-error bg-surface px-space-4 py-space-3 text-label">
    <div className="font-semibold text-error">Provider không khả dụng</div>
    <div className="mt-space-2 whitespace-pre-wrap text-primary">Nguyên nhân: {message.content}</div>
    <div className="mt-space-3 flex flex-wrap gap-space-2"><Button variant="ghost" size="sm" onClick={onRetry}>Thử lại</Button><Button variant="ghost" size="sm" onClick={() => { window.location.hash = '#/settings' }}>Mở Settings</Button></div>
  </div>
  const mine = message.role === 'user'
  return <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
    <div className="max-w-[78%]">
      <div className={`whitespace-pre-wrap rounded-[12px] px-space-4 py-space-3 text-label ${mine ? 'bg-accent-subtle text-primary' : 'bg-surface text-secondary'}`}>
        {message.role === 'assistant' && !message.streaming && !artifact ? <Markdown source={message.content} /> : message.content || (message.streaming ? '…' : '')}
      </div>
      {artifact && summary && <button onClick={onOpenArtifact} className="mt-space-2 flex w-full max-w-[340px] items-center gap-space-3 rounded-[10px] border border-border-subtle bg-elevated px-space-3 py-space-3 text-left transition-colors hover:border-accent">
        <span className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[7px] bg-accent-subtle text-accent">▤</span>
        <span className="min-w-0 flex-1"><span className="block truncate text-label font-semibold text-primary">{summary.title}</span><span className="block text-caption text-muted">{summary.chars} ký tự · {summary.items} mục</span></span>
        <span className="text-caption text-muted">→</span>
      </button>}
      {message.reasoning && <><Button variant="ghost" size="sm" className="mt-space-1" onClick={() => setShowReasoning(v => !v)}>{showReasoning ? 'Ẩn suy nghĩ' : 'Hiện suy nghĩ'}</Button>{showReasoning && <div className="mt-space-1 whitespace-pre-wrap border-l border-border-subtle pl-space-2 font-mono text-caption text-muted">{message.reasoning}</div>}</>}
      {message.content && !message.streaming && <div className="mt-space-1 flex gap-space-2"><Button variant="ghost" size="sm" onClick={onCopy}>Copy</Button>{message.role === 'assistant' && <Button variant="ghost" size="sm" onClick={pinned ? onUnpin : onPin}>{pinned ? 'Bỏ ghim' : 'Ghim'}</Button>}</div>}
    </div>
  </div>
}

function Composer({ value, onChange, onSubmit, onStop, streaming, placeholder, skillMatches, onPickSkill, onAttach }: {
  value: string; onChange: (v: string) => void; onSubmit: () => void; onStop: () => void; streaming: boolean; placeholder: string; skillMatches: string[]; onPickSkill: (name: string) => void; onAttach: () => void
}) {
  return <div className="p-space-4 pt-space-2">
    <div className="relative">
      {skillMatches.length > 0 && <div className="absolute bottom-full left-0 z-10 mb-space-1 w-full max-w-[280px] rounded-md border border-border-subtle bg-surface p-space-1">{skillMatches.map(name => <button key={name} onClick={() => onPickSkill(name)} className="block w-full rounded-sm px-space-2 py-space-1 text-left text-caption text-secondary hover:bg-hover">#{name}</button>)}</div>}
      <div className="flex items-end gap-space-2 rounded-[12px] border border-border-strong bg-surface py-space-2 pl-space-4 pr-space-2">
        <textarea aria-label="Nhập tin nhắn" value={value} onChange={e => onChange(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSubmit() } }}
          placeholder={placeholder} rows={1} className="max-h-[120px] flex-1 resize-none border-none bg-transparent py-space-1 text-label text-primary outline-none placeholder:text-muted" />
        <IconButton icon="📎" aria-label="Đính kèm file" onClick={onAttach} />
        {streaming
          ? <button aria-label="Dừng" onClick={onStop} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-error text-error">■</button>
          : <button aria-label="Gửi" onClick={onSubmit} disabled={!value.trim()} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent text-app disabled:opacity-40">➤</button>}
      </div>
    </div>
  </div>
}

// ── Right: artifact panel ──────────────────────────────────────────────────────
function ArtifactEmpty({ onOpenLibrary, count }: { onOpenLibrary: () => void; count: number }) {
  return <div className="flex flex-1 flex-col items-center justify-center p-space-8 text-center">
    <div className="mb-space-3 flex h-[44px] w-[44px] items-center justify-center rounded-[11px] bg-surface text-[19px] text-muted">▤</div>
    <div className="mb-space-1 text-label font-semibold text-primary">Chưa chọn artifact</div>
    <div className="max-w-[220px] text-caption text-muted">Artifact hiện ra đây khi AI tạo output tái dùng được.</div>
    {count > 0 && <Button variant="secondary" size="sm" className="mt-space-4" onClick={onOpenLibrary}>Mở thư viện ({count})</Button>}
  </div>
}

function ArtifactPanel({ message, focused, onFocus, onPopout, onHistory, onExport, onCopy, onEditSection, onSelection }: { message: Message; focused: boolean; onFocus: () => void; onPopout: () => void; onHistory: () => void; onExport: () => void; onCopy: () => void; onEditSection: (heading: string, action: string) => void; onSelection: (text: string, action: string) => void }) {
  const summary = artifactSummary(message.content)
  const sections = useMemo(() => splitSections(message.content), [message.content])
  const [selectedText, setSelectedText] = useState(''); const [selectionPoint, setSelectionPoint] = useState({ top: 0, left: 0 })
  const captureSelection = () => { const current = window.getSelection(); const text = current?.toString().trim() ?? ''; if (!text || !current?.rangeCount) { setSelectedText(''); return } const rect = current.getRangeAt(0).getBoundingClientRect(); setSelectedText(text); setSelectionPoint({ top: rect.bottom + 8, left: Math.max(8, rect.left) }) }
  return <>
    <div className="border-b border-border-subtle p-space-4">
      <div className="flex items-start justify-between gap-space-2">
        <div className="min-w-0 text-title font-bold text-primary">{summary.title}</div>
        <div className="flex shrink-0 gap-space-1">
          <button disabled className="rounded-md border border-border-subtle bg-elevated px-space-2 text-caption text-secondary">v1 · hiện tại</button>
          <IconButton icon={focused ? '↙' : '↗'} aria-label={focused ? 'Split view' : 'Focus'} onClick={onFocus} />
          <IconButton icon="□" aria-label="Pop-out" onClick={onPopout} />
          <IconButton icon="⏱" aria-label="Lịch sử phiên bản" onClick={onHistory} />
          <IconButton icon="⭳" aria-label="Xuất" onClick={onExport} />
          <IconButton icon="⧉" aria-label="Copy" onClick={onCopy} />
        </div>
      </div>
      <div className="mt-space-2 flex flex-wrap items-center gap-space-2">
        <span className="rounded-full bg-accent-subtle px-space-2 py-[3px] text-caption font-semibold text-accent">Draft</span>
        <span className="text-caption text-muted">document · v1</span>
        <span className="text-caption text-muted">· {summary.items} mục</span>
      </div>
    </div>
    <div className="relative min-h-0 flex-1 overflow-y-auto" onMouseUp={captureSelection}>
      {selectedText && <div className="fixed z-30 flex gap-1 rounded-md border border-border-strong bg-elevated p-1 shadow-lg" style={{ top: selectionPoint.top, left: selectionPoint.left }} onMouseDown={e => e.preventDefault()}>{['Hỏi AI', 'Viết lại', 'Rút gọn', 'Comment', 'Copy'].map(action => <button key={action} onClick={() => { onSelection(selectedText, action); setSelectedText('') }} className="rounded-sm px-space-2 py-space-1 text-caption text-primary hover:bg-hover">{action}</button>)}</div>}
      {sections.map((sec, i) => <ArtifactSection key={i} heading={sec.heading} body={sec.body} onAction={action => onEditSection(sec.heading, action)} />)}
    </div>
  </>
}
const sectionActions = ['Viết lại', 'Rút gọn', 'Mở rộng', 'Thêm ví dụ', 'Đổi giọng']
function ArtifactSection({ heading, body, onAction }: { heading: string; body: string; onAction: (action: string) => void }) {
  return <div className="border-b border-border-subtle p-space-4">
    <div className="mb-space-1 flex items-center justify-between">
      <div className="text-label font-bold text-primary">{heading}</div>
      <Popover align="end" label="⋯" aria-label={`Sửa phần ${heading}`} triggerClassName="!h-6 !w-6 !px-0" className="w-[180px]">
        {(close: () => void) => <div>{sectionActions.map(a => <button key={a} onClick={() => { onAction(a); close() }} className="block w-full rounded-sm px-space-2 py-space-1 text-left text-caption text-primary hover:bg-hover">{a}</button>)}</div>}
      </Popover>
    </div>
    <div className="whitespace-pre-wrap text-label text-secondary"><Markdown source={body} /></div>
  </div>
}
// Split an artifact into heading + body sections by markdown headings; the whole thing
// is one "Nội dung" section if it has none.
function splitSections(content: string): { heading: string; body: string }[] {
  const lines = content.split('\n'); const out: { heading: string; body: string[] }[] = []
  for (const line of lines) {
    const h = line.match(/^#{1,3}\s+(.*)/)
    if (h) out.push({ heading: h[1].trim(), body: [] })
    else if (out.length) out[out.length - 1].body.push(line)
    else { out.push({ heading: 'Nội dung', body: [line] }) }
  }
  return out.map(s => ({ heading: s.heading, body: s.body.join('\n').trim() })).filter(s => s.heading || s.body)
}

// ── Context drawer ─────────────────────────────────────────────────────────────
function ContextDrawer({ context, onChange, tooLarge, estimate, onClose }: { context: SharedContextState; onChange: (c: SharedContextState) => void; tooLarge: boolean; estimate: number; onClose: () => void }) {
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [onClose])
  const toggleInstruction = (id: string) => onChange({ ...context, instructions: context.instructions.map(i => i.id === id ? { ...i, active: !i.active } : i) })
  return <>
    <div onClick={onClose} className="fixed inset-0 z-40 bg-black/40" />
    <aside role="dialog" aria-modal="true" aria-label="Quản lý bối cảnh" className="fixed inset-y-0 right-0 z-50 flex w-[420px] max-w-[92vw] flex-col bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4">
        <div className="text-title font-bold text-primary">Quản lý bối cảnh</div>
        <IconButton icon="×" aria-label="Đóng" onClick={onClose} />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-space-4">
        {tooLarge && <div className="mb-space-4 rounded-[9px] border border-error bg-error-subtle p-space-3"><div className="mb-space-1 text-caption font-semibold text-error">Bối cảnh quá lớn.</div><div className="text-caption text-error">Bỏ bớt tin ghim hoặc rút gọn phần mô tả.</div></div>}
        <SidebarHeading>Mô tả chung</SidebarHeading>
        <Textarea value={context.text} onChange={e => onChange({ ...context, text: e.target.value })} placeholder="Mục tiêu, ràng buộc, quyết định đã chốt…" rows={4} className="resize-y text-body" aria-label="Mô tả bối cảnh" />
        <div className="mt-space-4"><SidebarHeading>Tin ghim ({context.pinned.length}/10)</SidebarHeading></div>
        {context.pinned.length === 0 && <p className="text-caption text-muted">Chưa ghim tin nào. Ghim từ tin nhắn của AI.</p>}
        {context.pinned.map(item => <label key={item.id} className="flex items-center gap-space-2 py-space-2"><input type="checkbox" checked onChange={() => onChange({ ...context, pinned: context.pinned.filter(p => p.id !== item.id) })} className="h-[15px] w-[15px] shrink-0" /><span className="min-w-0 flex-1 truncate text-label text-primary">{item.content}</span></label>)}
        <div className="mt-space-4"><SidebarHeading>Files</SidebarHeading></div>
        <p className="text-caption text-muted">Chưa có file. <span className="text-tertiary">(backend chưa nối)</span></p>
        <div className="mt-space-4"><SidebarHeading>Hướng dẫn</SidebarHeading></div>
        {context.instructions.map(i => <label key={i.id} className="flex items-center gap-space-2 py-space-2"><input type="checkbox" checked={i.active} onChange={() => toggleInstruction(i.id)} className="h-[15px] w-[15px] shrink-0" /><span className="text-label text-primary">{i.label}</span></label>)}
        <div className="mt-space-4 flex items-center justify-between rounded-[9px] bg-elevated p-space-3 text-caption text-secondary"><span>Ước tính bối cảnh</span><b className={tooLarge ? 'text-error' : 'text-success'}>~{formatTokens(estimate)} token</b></div>
      </div>
      <div className="flex gap-space-2 border-t border-border-subtle p-space-4">
        <Button variant="secondary" className="flex-1 justify-center" onClick={() => onChange({ ...context, text: '', pinned: [] })}>Xoá</Button>
        <Button variant="primary" className="flex-1 justify-center" onClick={onClose}>Áp dụng</Button>
      </div>
    </aside>
  </>
}

// ── Version history (stub: no artifact versioning backend yet) ──────────────────
function VersionHistoryModal({ message, onClose }: { message: Message; onClose: () => void }) {
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [onClose])
  const summary = artifactSummary(message.content)
  return <div onClick={onClose} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-space-4">
    <div role="dialog" aria-modal="true" onClick={e => e.stopPropagation()} className="flex h-[520px] max-h-[86vh] w-[880px] max-w-[92vw] flex-col overflow-hidden rounded-[14px] bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4"><div className="text-title font-bold text-primary">Lịch sử phiên bản — {summary.title}</div><IconButton icon="×" aria-label="Đóng" onClick={onClose} /></div>
      <div className="flex min-h-0 flex-1">
        <div className="w-[280px] shrink-0 overflow-y-auto border-r border-border-subtle p-space-3">
          <div className="rounded-[9px] bg-hover p-space-3"><div className="flex items-center gap-space-2"><span className="text-label font-bold text-primary">v1</span><span className="rounded-full bg-accent-subtle px-space-2 py-[1px] text-caption font-semibold text-accent">HIỆN TẠI</span></div><div className="mt-[3px] text-caption text-secondary">Bản đầu tiên</div></div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-space-4">
          <div className="rounded-[9px] border border-border-subtle bg-elevated p-space-4 text-caption text-muted">Chưa có phiên bản trước để so sánh. Versioning artifact chưa nối backend — <span className="text-tertiary">TODO(backend)</span>.</div>
        </div>
      </div>
      <div className="flex justify-end border-t border-border-subtle p-space-4"><Button variant="secondary" onClick={onClose}>Đóng</Button></div>
    </div>
  </div>
}

// ── Export modal (markdown/text/json/html are real; PDF + share are stubs) ──────
const exportFormats = [{ id: 'markdown', label: 'Markdown' }, { id: 'text', label: 'Text' }, { id: 'json', label: 'JSON' }, { id: 'html', label: 'HTML' }, { id: 'pdf', label: 'PDF (chưa nối)' }]
function ExportModal({ message, onClose, onToast }: { message: Message; onClose: () => void; onToast: (t: string) => void }) {
  const [format, setFormat] = useState('markdown')
  const [withTitle, setWithTitle] = useState(true)
  const summary = artifactSummary(message.content)
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [onClose])
  const render = () => {
    const head = withTitle ? `${summary.title}\n\n` : ''
    if (format === 'json') return JSON.stringify({ title: summary.title, content: message.content }, null, 2)
    if (format === 'html') return `${withTitle ? `<h1>${summary.title}</h1>\n` : ''}<pre>${message.content}</pre>`
    return head + message.content
  }
  const mime = format === 'json' ? 'application/json' : format === 'html' ? 'text/html' : 'text/markdown'
  const ext = format === 'json' ? 'json' : format === 'html' ? 'html' : format === 'text' ? 'txt' : 'md'
  const download = () => { if (format === 'pdf') { onToast('PDF: backend chưa nối'); return } const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([render()], { type: mime })); a.download = `${summary.title.slice(0, 40) || 'artifact'}.${ext}`; a.click(); URL.revokeObjectURL(a.href); onToast('Đã tải xuống') }
  return <div onClick={onClose} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-space-4">
    <div role="dialog" aria-modal="true" onClick={e => e.stopPropagation()} className="w-[480px] max-w-[92vw] overflow-hidden rounded-[14px] bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4"><div className="text-title font-bold text-primary">Xuất artifact</div><IconButton icon="×" aria-label="Đóng" onClick={onClose} /></div>
      <div className="max-h-[60vh] overflow-y-auto p-space-4">
        <div className="mb-space-4 text-label text-secondary">{summary.title} · document</div>
        <SidebarHeading>Định dạng</SidebarHeading>
        <div className="mb-space-4 grid grid-cols-2 gap-space-2">{exportFormats.map(f => <label key={f.id} className={`flex items-center gap-space-2 rounded-md border px-space-3 py-space-2 ${format === f.id ? 'border-accent bg-accent-subtle' : 'border-border-subtle'}`}><input type="radio" name="fmt" checked={format === f.id} onChange={() => setFormat(f.id)} className="h-[14px] w-[14px]" /><span className="text-caption text-primary">{f.label}</span></label>)}</div>
        <SidebarHeading>Tuỳ chọn</SidebarHeading>
        <label className="flex items-center gap-space-2 py-space-1"><input type="checkbox" checked={withTitle} onChange={() => setWithTitle(v => !v)} className="h-[15px] w-[15px]" /><span className="text-label text-primary">Kèm tiêu đề</span></label>
        <div className="mt-space-4"><SidebarHeading>Xem trước</SidebarHeading></div>
        <pre className="max-h-[120px] overflow-y-auto whitespace-pre-wrap rounded-md border border-border-subtle bg-elevated p-space-3 font-mono text-caption text-secondary">{render().slice(0, 600)}</pre>
      </div>
      <div className="flex gap-space-2 border-t border-border-subtle p-space-4">
        <Button variant="secondary" onClick={() => { void navigator.clipboard?.writeText(render()); onToast('Đã copy') }}>Copy</Button>
        <Button variant="secondary" onClick={() => onToast('Share link: backend chưa nối')}>Chia sẻ link</Button>
        <div className="flex-1" />
        <Button variant="primary" onClick={download}>Tải xuống</Button>
      </div>
    </div>
  </div>
}
