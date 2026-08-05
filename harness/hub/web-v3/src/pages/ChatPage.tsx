import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { api, apiRequest } from '../lib/api'
import { parseSse } from '../lib/sse'
import { Markdown } from '../lib/markdown'
import { artifactSummary, isArtifact } from '../lib/artifact'
import { Button, Chip, IconButton, Popover, ProviderDot, Textarea } from '../lib/ui'
import { asProviderId, providerIds } from '../lib/uiHelpers'
import { t } from '../lib/i18n'
import { Archive, ArrowLeft, ArrowRight, Check, ChevronDown, ChevronLeft, ChevronRight, Clipboard, Download, Ellipsis, ExternalLink, FileText, History, MessageCircle, Paperclip, Pin, PinOff, Plus, RotateCcw, Send, Settings, Square, X } from 'lucide-react'

// ── AI Chat Workspace ─────────────────────────────────────────────────────────
// Three-panel workspace (imported from the "AI Workspace" design system, mapped to
// the hub token set): top bar · sidebar (Chats/Files/Artifacts) · chat · artifact.
// A single active chat is the primary shape; the model picker, context, artifact
// panel, version history and export all hang off it. Chat, models, providers,
// agents, skills and artifact version history are wired to the real backend;
// Files, artifacts and comments are backed by the server too; export offers only
// the formats it can actually produce.

type Provider = { id: string; available: boolean; version?: string; detail: string; capabilities?: { stream?: boolean; resume?: boolean; models?: number } }
type Catalog = { id: string; shortName?: string; category?: string; label?: string }
type Skill = { id: string; name?: string; title?: string; description?: string }
type ActiveSkill = { id: string; scope: 'turn' | 'window' }
type Message = { id?: string; artifactId?: string; role: 'user' | 'assistant' | 'system'; content: string; reasoning?: string; usage?: Record<string, unknown>; streaming?: boolean }
type ArtifactVersion = { version: string; created_at: string; content: string }
type StoredArtifact = { id: string; title: string; versions: ArtifactVersion[] }
type Chat = { id: string; title: string; provider: string; model: string; agentId?: string; cliSessionId?: string; messages: Message[]; notice?: string; updatedAt: number }
type ChatFile = { name: string; size: number; updated_at: number }
type ArtifactComment = { id: string; quoted_text: string; author: string; body: string; created_at: string; resolved: boolean }
type PinnedMessage = { id: string; content: string }
type Instruction = { id: string; label: string; active: boolean }
type SharedContextState = { text: string; pinned: PinnedMessage[]; instructions: Instruction[] }

const chatsKey = 'hub-v3-chats'
const sharedContextKey = 'hub-v3-shared-context'
const artifactWidthKey = 'hub-v3-artifact-width'
const asKind = asProviderId
const artifactActionKeys = ['chat.action.analyzeDocument', 'chat.action.summarize', 'chat.action.shorten', 'chat.action.rewrite', 'chat.action.createSlides', 'chat.action.askAboutData'] as const
const selectionActionKeys = ['chat.selection.askAi', 'chat.action.rewrite', 'chat.action.shorten', 'chat.selection.comment', 'chat.copy'] as const

// Honest, provider-level capability copy — no fabricated per-model speed/cost ratings.
const providerRole: Record<string, { role: string; note: string }> = {
  claude: { role: t('chat.provider.claudeRole'), note: t('chat.provider.claudeNote') },
  codex: { role: t('chat.provider.codexRole'), note: t('chat.provider.codexNote') },
  nvidia: { role: t('chat.provider.nvidiaRole'), note: t('chat.provider.nvidiaNote') },
}

const formatTokens = (value: number) => value < 1000 ? String(value) : value < 1e6 ? `${(value / 1000).toFixed(1).replace(/\.0$/, '')}k` : `${(value / 1e6).toFixed(1).replace(/\.0$/, '')}M`
const estimateTokens = (text: string) => Math.ceil(text.length / 4)

const defaultInstructions: Instruction[] = [{ id: 'i1', label: t('chat.defaultInstruction'), active: true }]
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
const promptFor = (context: SharedContextState, text: string, inject: boolean, extra = '') => { const contextText = [sharedText(context), extra].filter(Boolean).join('\n\n'); return inject && contextText ? `${t('chat.sharedContext')}\n${contextText}\n\n${t('chat.request')}\n${text}` : text }

const providerState = (provider?: Provider) => {
  if (!provider?.available) {
    const detail = provider?.detail?.toLowerCase() ?? ''
    if (/not set|not configured|environment|api key|token/.test(detail)) return { label: t('chat.provider.setupRequired'), kind: 'setup-required' as const }
    if (detail === 'not_installed') return { label: t('chat.provider.notInstalled'), kind: 'not-installed' as const }
    return { label: t('chat.provider.unavailable'), kind: 'error' as const }
  }
  return { label: t('chat.provider.ready'), kind: 'ready' as const }
}

const makeChat = (provider = 'nvidia', model = ''): Chat => ({ id: crypto.randomUUID(), title: t('chat.newChat'), provider, model, messages: [], updatedAt: Date.now() })
const loadChats = (): Chat[] => { try { const v = JSON.parse(localStorage.getItem(chatsKey) ?? 'null'); return Array.isArray(v) && v.length ? v : [makeChat()] } catch { return [makeChat()] } }
const chatSubtitle = (chat: Chat) => { const last = [...chat.messages].reverse().find(m => m.content.trim()); return last ? last.content.replace(/\s+/g, ' ').slice(0, 42) : t('chat.noMessages') }
const modelShort = (chat: Chat, catalog: Catalog[]) => chat.model ? (catalog.find(m => m.id === chat.model)?.shortName ?? chat.model.split('/').at(-1) ?? chat.model) : t('chat.cliDefault')
const activeChatHandoffKey = 'hub-v3-active-chat'

export default function ChatPage() {
  const [chats, setChats] = useState<Chat[]>(loadChats)
  const [activeChatId, setActiveChatId] = useState<string>(() => loadChats()[0].id)
  const [leftTab, setLeftTab] = useState<'chats' | 'files' | 'artifacts'>('chats')
  const [sessionsCollapsed, setSessionsCollapsed] = useState(() => localStorage.getItem('hub-v3-sessions-collapsed') === 'true')
  const [sessionsDrawerOpen, setSessionsDrawerOpen] = useState(false)
  // Below 1280px the sessions column is a full-width drawer (position: fixed, see index.css),
  // not a collapsible dock — the desktop-only `sessionsCollapsed` preference must not hide its
  // content there. WorkspaceSidebar hides content via JSX (not CSS), so the viewport check has
  // to happen in React; matchMedia + a change listener keeps it live across resizes.
  const [sessionsCollapseActive, setSessionsCollapseActive] = useState(() => window.matchMedia('(min-width: 1280px)').matches)
  useEffect(() => {
    const query = window.matchMedia('(min-width: 1280px)')
    const onChange = (event: MediaQueryListEvent) => setSessionsCollapseActive(event.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])
  const sessionsCollapsedEffective = sessionsCollapsed && sessionsCollapseActive
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
  const [artifactPanelOpen, setArtifactPanelOpen] = useState(false)
  const [artifactAutoOpened, setArtifactAutoOpened] = useState<Record<string, true>>({})
  const [artifactDismissed, setArtifactDismissed] = useState<Record<string, true>>({})
  const [artifactWidth, setArtifactWidth] = useState(() => {
    const saved = Number(localStorage.getItem(artifactWidthKey))
    return Number.isFinite(saved) ? Math.min(560, Math.max(320, saved)) : 400
  })
  const artifactReopen = useRef<HTMLButtonElement>(null)
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const [showExport, setShowExport] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const [serverArtifactCount, setServerArtifactCount] = useState(0)
  const [chatFiles, setChatFiles] = useState<ChatFile[]>([])
  const [comments, setComments] = useState<ArtifactComment[]>([])
  useEffect(() => { localStorage.setItem('hub-v3-sessions-collapsed', String(sessionsCollapsed)) }, [sessionsCollapsed])
  useEffect(() => { localStorage.setItem(artifactWidthKey, String(artifactWidth)) }, [artifactWidth])
  const fileInput = useRef<HTMLInputElement>(null)
  const controllers = useRef(new Map<string, AbortController>())
  const streamingMessageIds = useRef(new Map<string, string>())
  const toastTimer = useRef<number | undefined>(undefined)

  const activeChat = chats.find(c => c.id === activeChatId) ?? chats[0]
  const artifactMessages = useMemo(() => activeChat.messages.map((m, index) => ({ m, index })).filter(({ m }) => isArtifact(m)), [activeChat])
  const activeArtifact = activeArtifactIndex != null && isArtifact(activeChat.messages[activeArtifactIndex]) ? activeChat.messages[activeArtifactIndex] : null
  const isEmptyPhase = activeChat.messages.length === 0

  useEffect(() => { localStorage.setItem(chatsKey, JSON.stringify(chats.map(c => ({ ...c, messages: c.messages.map(({ streaming: _s, ...m }) => m) })))) }, [chats])
  useEffect(() => { localStorage.setItem(sharedContextKey, JSON.stringify(sharedContext)) }, [sharedContext])
  useEffect(() => { setActiveArtifactIndex(null) }, [activeChatId])
  useEffect(() => {
    if (!artifactMessages.length) { setArtifactPanelOpen(false); return }
    if (!artifactAutoOpened[activeChatId] && !artifactDismissed[activeChatId] && window.innerWidth >= 1600) {
      setActiveArtifactIndex(artifactMessages.at(-1)?.index ?? null)
      setArtifactPanelOpen(true)
      setArtifactAutoOpened(current => ({ ...current, [activeChatId]: true }))
    }
  }, [activeChatId, artifactAutoOpened, artifactDismissed, artifactMessages])
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
  useEffect(() => { void api<{ artifacts: { id: string }[] }>('/api/artifacts').then(data => { localStorage.setItem('hub-v3-artifacts', JSON.stringify(data.artifacts)); setServerArtifactCount(data.artifacts.length) }).catch(() => undefined) }, [])
  useEffect(() => { void api<ChatFile[]>(`/api/chats/${encodeURIComponent(activeChatId)}/files`).then(setChatFiles).catch(() => setChatFiles([])) }, [activeChatId])
  useEffect(() => { if (!activeArtifact?.artifactId) { setComments([]); return } void api<{ comments: ArtifactComment[] }>(`/api/artifacts/${encodeURIComponent(activeArtifact.artifactId)}/comments`).then(data => setComments(data.comments)).catch(() => setComments([])) }, [activeArtifact?.artifactId])

  const showToast = (text: string) => { setToast(text); window.clearTimeout(toastTimer.current); toastTimer.current = window.setTimeout(() => setToast(null), 2400) }
  const patch = (id: string, change: Partial<Chat>) => setChats(current => current.map(c => c.id === id ? { ...c, ...change, updatedAt: Date.now() } : c))
  const patchLast = (id: string, change: Partial<Message> | ((m: Message) => Partial<Message>)) => { const messageId = streamingMessageIds.current.get(id); if (!messageId) return; setChats(current => current.map(c => c.id === id ? { ...c, messages: c.messages.map(m => m.id === messageId ? { ...m, ...(typeof change === 'function' ? change(m) : change) } : m) } : c)) }
  const patchMessage = (chatId: string, messageId: string, change: Partial<Message>) => setChats(current => current.map(chat => chat.id === chatId ? { ...chat, messages: chat.messages.map(message => message.id === messageId ? { ...message, ...change } : message) } : chat))

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
    const chat = chats.find(c => c.id === activeChatId); if (!chat || controllers.current.has(activeChatId)) return
    const artifactContext = artifactContextEnabled && activeArtifact ? `${t('chat.artifactOpenContext')}\n${activeArtifact.content}` : ''
    const fingerprint = `${sharedContext.text}\n${sharedContext.pinned.map(i => i.id).join('|')}\n${activeInstructionText(sharedContext).join('|')}\n${artifactContext}`
    const shouldInject = Boolean(sharedText(sharedContext) || artifactContext) && (!chat.messages.some(m => m.role === 'user') || injectedContext[chat.id] !== fingerprint)
    const prompt = promptFor(sharedContext, trimmed, shouldInject, artifactContext)
    const title = chat.messages.length === 0 ? trimmed.replace(/\s+/g, ' ').slice(0, 40) : chat.title
    const user: Message = { role: 'user', content: prompt }
    const assistantId = crypto.randomUUID()
    const assistant: Message = { id: assistantId, role: 'assistant', content: '', reasoning: '', streaming: true }
    let assistantContent = ''
    const history = [...chat.messages, user]
    patch(chat.id, { messages: [...history, assistant], title }); streamingMessageIds.current.set(chat.id, assistantId)
    const controller = new AbortController(); controllers.current.set(chat.id, controller)
    const providerInfo = providers.find(p => p.id === chat.provider)
    if (providerInfo && !providerInfo.available) { patchLast(chat.id, { role: 'system', content: providerInfo.detail || t('chat.providerUnavailable'), streaming: false }); controllers.current.delete(chat.id); return }
    // NVIDIA gets full history; CLI providers resume with only the new message when a session exists.
    const messages = (chat.provider !== 'nvidia' && chat.cliSessionId ? [user] : history).filter(m => m.role !== 'system')
    try {
      const response = await apiRequest('/api/chat', { method: 'POST', body: JSON.stringify({ provider: chat.provider, model: chat.model || undefined, agent_id: chat.agentId, messages, session_id: chat.cliSessionId, chat_id: chat.id, skills: selectedSkills.map(s => s.id) }), signal: controller.signal })
      if (!response.body) throw new Error(t('chat.streamUnavailable'))
      for await (const item of parseSse(response.body)) {
        const data = item.data as Record<string, unknown>
        if (item.event === 'reasoning') patchLast(chat.id, cur => ({ reasoning: `${cur.reasoning ?? ''}${String(data.text ?? '')}`, streaming: true }))
        if (item.event === 'delta') { const delta = String(data.text ?? ''); assistantContent += delta; patchLast(chat.id, cur => ({ content: `${cur.content}${delta}`, streaming: true })) }
        if (item.event === 'done') {
          if (shouldInject) setInjectedContext(c => ({ ...c, [chat.id]: fingerprint }))
          patchLast(chat.id, { streaming: false, usage: data.usage as Record<string, unknown> })
          patch(chat.id, { cliSessionId: typeof data.session_id === 'string' ? data.session_id : chat.cliSessionId, model: typeof data.model === 'string' && chat.provider === 'nvidia' ? data.model : chat.model, notice: typeof data.skill_notice === 'string' ? data.skill_notice : chat.notice })
          const content = assistantContent
          if (content && isArtifact({ role: 'assistant', content })) void api<{ id: string }>('/api/artifacts', { method: 'POST', body: JSON.stringify({ title: artifactSummary(content).title, content, source: 'chat' }) }).then(saved => { patchMessage(chat.id, assistantId, { artifactId: saved.id }); return api<{ artifacts: { id: string }[] }>('/api/artifacts') }).then(data => { localStorage.setItem('hub-v3-artifacts', JSON.stringify(data.artifacts)); setServerArtifactCount(data.artifacts.length) }).catch(() => undefined)
        }
        if (item.event === 'error') patchLast(chat.id, { role: 'system', content: String(data.message ?? t('chat.streamError')), streaming: false })
      }
    } catch (error) { if ((error as Error).name !== 'AbortError') patchLast(chat.id, { role: 'system', content: (error as Error).message, streaming: false }) }
    finally { patchLast(chat.id, { streaming: false }); controllers.current.delete(chat.id); streamingMessageIds.current.delete(chat.id) }
  }
  const submitPrompt = () => { const text = promptText.trim(); if (!text || controllers.current.has(activeChatId)) return; const selected = activeSkills; setPromptText(''); void send(text, selected); if (selected.some(s => s.scope === 'turn')) setActiveSkills(c => c.filter(s => s.scope !== 'turn')) }
  const stop = () => controllers.current.get(activeChatId)?.abort()
  const retry = () => { const prompt = [...activeChat.messages].reverse().find(m => m.role === 'user')?.content; if (prompt) void send(prompt) }
  const streaming = Boolean(activeChat.messages.at(-1)?.streaming)

  const pin = (index: number, content: string) => setSharedContext(cur => { if (cur.pinned.length >= 10) { showToast(t('chat.maxPins')); return cur } const id = `${activeChatId}:${index}`; return cur.pinned.some(i => i.id === id) ? cur : { ...cur, pinned: [...cur.pinned, { id, content }] } })
  const unpin = (id: string) => setSharedContext(cur => ({ ...cur, pinned: cur.pinned.filter(i => i.id !== id) }))
  const pinnedIds = new Set(sharedContext.pinned.map(i => i.id))
  // Section-level "edit" is a real backend round-trip: it sends a scoped follow-up prompt.
  const editSection = (heading: string, action: string) => { void send(t('chat.editSectionPrompt', { action, heading })); showToast(`${action} · ${heading}`) }

  const loadFiles = () => void api<ChatFile[]>(`/api/chats/${encodeURIComponent(activeChatId)}/files`).then(setChatFiles).catch(() => setChatFiles([]))
  const uploadFile = async (file: File) => { const form = new FormData(); form.append('file', file); try { await api(`/api/chats/${encodeURIComponent(activeChatId)}/files`, { method: 'POST', body: form }); loadFiles(); setLeftTab('files'); showToast(t('chat.fileUploaded')) } catch (error) { showToast(error instanceof Error ? error.message : t('chat.fileUploadFailed')) } }
  const ensureArtifact = async (message: Message) => { if (message.artifactId) return message.artifactId; const saved = await api<{ id: string }>('/api/artifacts', { method: 'POST', body: JSON.stringify({ title: artifactSummary(message.content).title, content: message.content, source: 'chat' }) }); setChats(current => current.map(chat => chat.id !== activeChatId ? chat : { ...chat, messages: chat.messages.map(item => item === message ? { ...item, artifactId: saved.id } : item) })); return saved.id }
  const addComment = async (text: string) => { if (!activeArtifact) return; const body = window.prompt(t('chat.commentPrompt')); if (!body?.trim()) return; try { const artifactId = await ensureArtifact(activeArtifact); const comment = await api<ArtifactComment>(`/api/artifacts/${encodeURIComponent(artifactId)}/comments`, { method: 'POST', body: JSON.stringify({ quoted_text: text, author: t('chat.you'), body }) }); setComments(current => [...current, comment]); showToast(t('chat.commentAdded')) } catch (error) { showToast(error instanceof Error ? error.message : t('chat.commentAddFailed')) } }
  const popoutArtifact = async () => { if (!activeArtifact) return; try { window.location.hash = `#/artifacts/${encodeURIComponent(await ensureArtifact(activeArtifact))}` } catch (error) { showToast(error instanceof Error ? error.message : t('chat.artifactOpenFailed')) } }
  const setCommentResolved = async (comment: ArtifactComment, resolved: boolean) => { if (!activeArtifact?.artifactId) return; try { const saved = await api<ArtifactComment>(`/api/artifacts/${encodeURIComponent(activeArtifact.artifactId)}/comments/${encodeURIComponent(comment.id)}`, { method: 'PATCH', body: JSON.stringify({ resolved }) }); setComments(current => current.map(item => item.id === saved.id ? saved : item)) } catch (error) { showToast(error instanceof Error ? error.message : t('chat.commentUpdateFailed')) } }
  const deleteComment = async (comment: ArtifactComment) => { if (!activeArtifact?.artifactId) return; try { await api(`/api/artifacts/${encodeURIComponent(activeArtifact.artifactId)}/comments/${encodeURIComponent(comment.id)}`, { method: 'DELETE' }); setComments(current => current.filter(item => item.id !== comment.id)) } catch (error) { showToast(error instanceof Error ? error.message : t('chat.commentDeleteFailed')) } }
  const contextEstimate = estimateTokens([sharedText(sharedContext), artifactContextEnabled && activeArtifact?.content].filter(Boolean).join('\n\n'))
  const contextTooLarge = contextEstimate > 8000
  const contextSummary = t('chat.contextSummary', { tokens: formatTokens(contextEstimate), count: sharedContext.pinned.length })
  const resizeArtifact = (next: number) => setArtifactWidth(Math.min(560, Math.max(320, next)))
  const beginArtifactResize = (event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault()
    const startX = event.clientX; const startWidth = artifactWidth
    const onMove = (move: MouseEvent) => resizeArtifact(startWidth - (move.clientX - startX))
    const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
    window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp)
  }
  const openArtifactPanel = () => { setArtifactPanelOpen(true); if (activeArtifactIndex == null && artifactMessages.length) setActiveArtifactIndex(artifactMessages.at(-1)?.index ?? null); window.requestAnimationFrame(() => document.querySelector<HTMLButtonElement>('[data-artifact-close]')?.focus()) }
  const closeArtifactPanel = () => { setArtifactPanelOpen(false); setArtifactFocus(false); setArtifactDismissed(current => ({ ...current, [activeChatId]: true })); window.requestAnimationFrame(() => artifactReopen.current?.focus()) }

  return <div className="chat-workspace">
    <TopBar chat={activeChat} catalog={catalog} providers={providers} defaultModel={defaultModel}
      onChooseModel={chooseModel} exportDisabled={!activeArtifact} onExport={() => setShowExport(true)} onSettings={() => { window.location.hash = '#/settings' }} />
    <div data-artifact={artifactPanelOpen ? 'open' : 'closed'} className={`cw-body ${artifactFocus ? 'artifact-focus' : ''} ${sessionsCollapsedEffective ? 'sessions-collapsed' : ''} ${sessionsDrawerOpen ? 'sessions-drawer-open' : ''}`} style={{ '--cw-artifact-width': `${artifactWidth}px` } as CSSProperties}>
      <WorkspaceSidebar tab={leftTab} onTab={setLeftTab} chats={chats} activeChatId={activeChatId} onNewChat={newChat} onSelectChat={id => { selectChat(id); setSessionsDrawerOpen(false) }}
        artifacts={artifactMessages} activeArtifactIndex={activeArtifactIndex} onSelectArtifact={i => { setActiveArtifactIndex(i); setSessionsDrawerOpen(false) }} files={chatFiles} onUploadFile={() => fileInput.current?.click()} onDeleteFile={async name => { await api(`/api/chats/${encodeURIComponent(activeChatId)}/files/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadFiles() }} collapsed={sessionsCollapsedEffective} onToggle={() => setSessionsCollapsed(value => !value)} />
      <button type="button" className="cw-sidebar-scrim" aria-label={t('common.close')} onClick={() => setSessionsDrawerOpen(false)} />

      <div className="cw-center">
        <button type="button" className="cw-drawer-toggle" aria-label={t('chat.expandChats')} onClick={() => setSessionsDrawerOpen(true)}><MessageCircle size={16} strokeWidth={1.75} aria-hidden="true" /></button>
        {/* Context bar only once a conversation exists; the composer is always present. */}
        {!isEmptyPhase && <div className="flex items-center gap-space-2 border-b border-border-subtle px-space-4 py-space-2 text-caption text-secondary">
          <span className="min-w-0 truncate">{contextSummary}</span>{activeArtifact && <button onClick={() => setArtifactContextEnabled(v => !v)} className={`shrink-0 rounded-full border px-space-2 py-[3px] ${artifactContextEnabled ? 'border-accent bg-accent-subtle text-accent' : 'border-border-subtle text-muted'}`}>{t('chat.contextArtifact', { artifact: artifactSummary(activeArtifact.content).title, chat: activeChat.title })}</button>}
          <Button variant="ghost" size="sm" className="shrink-0" onClick={() => setContextOpen(true)}>{t('chat.manage')}</Button>
        </div>}
        <div className="cw-msgs">
          {isEmptyPhase
            ? <EmptyState onCreate={() => void send(t('chat.createLaunchPlan'))} />
            : <div className="cw-reading-column">
              {activeChat.notice && <SystemEvent text={activeChat.notice} />}
              {activeChat.messages.map((m, i) => <MessageView key={i} message={m} last={i === activeChat.messages.length - 1}
                onOpenArtifact={() => { setActiveArtifactIndex(i); setLeftTab('artifacts'); openArtifactPanel() }} onRetry={retry} onCopy={() => { void navigator.clipboard?.writeText(m.content); showToast(t('chat.copied')) }}
                pinned={pinnedIds.has(`${activeChatId}:${i}`)} onPin={() => pin(i, m.content)} onUnpin={() => unpin(`${activeChatId}:${i}`)} />)}
              {streaming && !activeChat.messages.at(-1)?.content && <ThinkingDots />}
            </div>}
        </div>
        {!isEmptyPhase && activeArtifact && <div className="flex flex-wrap gap-space-2 px-space-4 pt-space-2">{artifactActionKeys.map(key => { const action = t(key); return <button key={key} onClick={() => void send(t('chat.openDocumentPrompt', { action }))} className="shrink-0 whitespace-nowrap rounded-full border border-border-strong bg-surface px-space-3 py-[6px] text-caption text-secondary transition-colors hover:border-accent hover:text-accent">{action}</button> })}</div>}
        <Composer value={promptText} onChange={changePrompt} onSubmit={() => { if (!streaming) submitPrompt() }} onStop={stop} streaming={streaming}
          placeholder={t('chat.messageProvider', { provider: activeChat.provider })} skillMatches={skillMatches.map(skillName)} onPickSkill={name => { activateSkill(name); setPromptText('') }}
          onAttach={() => fileInput.current?.click()} skills={skills.map(skillName)} onActivateSkill={name => activateSkill(name)} activeSkills={activeSkills} onRemoveSkill={removeSkill} providerLabel={`${activeChat.provider} · ${modelShort(activeChat, catalog)}`} />
      </div>

      <div className="cw-artifact">
        <div className="cw-artifact-resizer" role="separator" aria-orientation="vertical" aria-label={t('chat.resizeArtifact')} tabIndex={0} onMouseDown={beginArtifactResize} onKeyDown={event => { if (event.key === 'ArrowLeft') { event.preventDefault(); resizeArtifact(artifactWidth + 16) } if (event.key === 'ArrowRight') { event.preventDefault(); resizeArtifact(artifactWidth - 16) } }} />
        {activeArtifact
          ? <ArtifactPanel message={activeArtifact} comments={comments} focused={artifactFocus} onClose={closeArtifactPanel} onFocus={() => setArtifactFocus(v => !v)} onPopout={() => void popoutArtifact()} onHistory={() => setShowVersionHistory(true)} onExport={() => setShowExport(true)} onCopy={() => { void navigator.clipboard?.writeText(activeArtifact.content); showToast(t('chat.copied')) }} onEditSection={editSection} onResolveComment={setCommentResolved} onDeleteComment={deleteComment} onSelection={(text, action) => { if (action === t('chat.copy')) { void navigator.clipboard?.writeText(text); showToast(t('chat.selectionCopied')); return } if (action === t('chat.selection.comment')) { void addComment(text); return } void send(`${action} the following text:\n"${text}"`) }} />
          : <ArtifactEmpty onClose={closeArtifactPanel} onOpenLibrary={() => setLeftTab('artifacts')} count={Math.max(artifactMessages.length, serverArtifactCount)} />}
      </div>
      {artifactMessages.length > 0 && !artifactPanelOpen && <button ref={artifactReopen} type="button" className="cw-artifact-reopen" aria-label={t('chat.openArtifact')} title={t('chat.openArtifact')} onClick={openArtifactPanel}><ChevronLeft size={16} strokeWidth={1.75} /></button>}
    </div>

    {contextOpen && <ContextDrawer context={sharedContext} onChange={setSharedContext} tooLarge={contextTooLarge} estimate={contextEstimate} onClose={() => setContextOpen(false)} />}
    {showVersionHistory && activeArtifact && <VersionHistoryModal message={activeArtifact} onClose={() => setShowVersionHistory(false)} />}
    {showExport && activeArtifact && <ExportModal message={activeArtifact} onClose={() => setShowExport(false)} onToast={showToast} />}
    <input ref={fileInput} className="hidden" type="file" onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) void uploadFile(file) }} />
    {toast && <div role="status" className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-full bg-elevated px-space-4 py-space-2 text-caption font-medium text-primary shadow-lg ring-1 ring-border-strong">{toast}</div>}
  </div>
}

// ── Top bar ───────────────────────────────────────────────────────────────────
function TopBar({ chat, catalog, providers, defaultModel, onChooseModel, exportDisabled, onExport, onSettings }: {
  chat: Chat; catalog: Catalog[]; providers: Provider[]; defaultModel: string
  onChooseModel: (provider: string, model: string) => void; exportDisabled: boolean; onExport: () => void; onSettings: () => void
}) {
  const label = `${chat.provider} · ${modelShort(chat, catalog)}`
  return <div className="flex h-full items-center justify-between gap-space-3 border-b border-border-subtle bg-sidebar px-space-4">
    {/* Session identity, not product identity: the sidebar brand block already names the product. */}
    <div className="flex min-w-0 items-center gap-space-2">
      <div className="truncate text-label font-semibold text-primary">{chat.title}</div>
    </div>
    <div className="flex shrink-0 items-center gap-space-2">
      <ModelSelector chat={chat} catalog={catalog} providers={providers} defaultModel={defaultModel} triggerLabel={label} onChoose={onChooseModel} />
      <div className="h-5 w-px bg-border-subtle" />
      <Button variant="secondary" size="sm" disabled={exportDisabled} title={exportDisabled ? t('chat.noArtifactSelected') : undefined} onClick={onExport}>{t('chat.export')}</Button>
      <IconButton icon={<Settings size={16} strokeWidth={1.75} />} aria-label={t('chat.settings')} title={t('chat.settings')} className="!h-10 !w-10" onClick={onSettings} />
    </div>
  </div>
}

function ModelSelector({ chat, catalog, providers, defaultModel, triggerLabel, onChoose }: {
  chat: Chat; catalog: Catalog[]; providers: Provider[]; defaultModel: string; triggerLabel: string; onChoose: (provider: string, model: string) => void
}) {
  const grouped = useMemo(() => catalog.reduce<Record<string, Catalog[]>>((all, m) => { const key = m.category ?? 'Models'; (all[key] ??= []).push(m); return all }, {}), [catalog])
  const cards: Provider[] = providerIds.map(id => providers.find(p => p.id === id) ?? { id, available: false, detail: t('chat.provider.unavailable') })
  return <Popover align="end" aria-label={t('chat.selectModel')} triggerClassName="max-w-[260px]" className="w-[340px] max-h-[70vh] overflow-y-auto"
    label={<span className="flex min-w-0 items-center gap-[7px]"><span className="h-[7px] w-[7px] shrink-0 rounded-full bg-accent" /><span className="truncate text-label">{triggerLabel}</span><ChevronDown aria-hidden="true" size={16} strokeWidth={1.75} className="shrink-0 text-muted" /></span>}>
    {(close: () => void) => <div className="space-y-space-1">
      <div className="px-space-2 pb-space-1 text-section font-semibold uppercase tracking-section text-muted">{t('chat.selectModel')}</div>
      {cards.map(p => {
        const state = providerState(p); const role = providerRole[p.id] ?? { role: '', note: '' }; const selected = chat.provider === p.id
        const caps = p.capabilities
        return <div key={p.id} className={`rounded-[9px] border p-space-3 ${selected ? 'border-accent bg-accent-subtle' : 'border-transparent'}`}>
          <button disabled={!p.available} onClick={() => { onChoose(p.id, p.id === 'nvidia' ? (chat.model || defaultModel) : ''); if (p.id !== 'nvidia') close() }}
            className="block w-full text-left disabled:cursor-not-allowed disabled:opacity-50">
            <div className="flex items-center justify-between gap-space-2">
              <span className="flex items-center gap-space-2 text-label font-semibold text-primary"><ProviderDot provider={asKind(p.id)} />{p.id}{selected && <Check aria-hidden="true" size={16} strokeWidth={1.75} className="text-accent" />}</span>
              <span className={`text-caption ${state.kind === 'ready' ? 'text-success' : state.kind === 'error' ? 'text-error' : 'text-muted'}`}>{state.label}</span>
            </div>
            <div className="mt-[2px] text-caption text-secondary">{role.role}</div>
            <div className="mt-[2px] text-caption text-muted">{role.note}{p.version ? ` · ${p.version}` : ''}</div>
            {caps && <div className="mt-space-1 flex gap-space-3 text-caption text-muted">{caps.stream != null && <span>{t('chat.stream')}: <b className="text-secondary">{caps.stream ? <Check aria-label={t('provider.available')} size={16} strokeWidth={1.75} /> : t('common.notAvailable')}</b></span>}{caps.resume != null && <span>{t('chat.resume')}: <b className="text-secondary">{caps.resume ? <Check aria-label={t('provider.available')} size={16} strokeWidth={1.75} /> : t('common.notAvailable')}</b></span>}{caps.models != null && <span>{t('chat.model')}: <b className="text-secondary">{caps.models}</b></span>}</div>}
          </button>
          {selected && p.id === 'nvidia' && <label className="mt-space-2 block space-y-space-1 text-caption text-muted">{t('chat.specificModel')}
            <select value={chat.model || defaultModel} onChange={e => onChoose('nvidia', e.target.value)} className="h-input w-full rounded-md border border-border-subtle bg-elevated px-space-3 text-body text-primary">
              {Object.entries(grouped).map(([category, models]) => <optgroup key={category} label={category}>{models.map(m => <option key={m.id} value={m.id}>{m.shortName ?? m.label ?? m.id}</option>)}</optgroup>)}
            </select></label>}
        </div>
      })}
    </div>}
  </Popover>
}

// ── Left sidebar ────────────────────────────────────────────────────────────────
function WorkspaceSidebar({ tab, onTab, chats, activeChatId, onNewChat, onSelectChat, artifacts, activeArtifactIndex, onSelectArtifact, files, onUploadFile, onDeleteFile, collapsed, onToggle }: {
  tab: 'chats' | 'files' | 'artifacts'; onTab: (t: 'chats' | 'files' | 'artifacts') => void
  chats: Chat[]; activeChatId: string; onNewChat: () => void; onSelectChat: (id: string) => void
  artifacts: { m: Message; index: number }[]; activeArtifactIndex: number | null; onSelectArtifact: (i: number) => void; files: ChatFile[]; onUploadFile: () => void; onDeleteFile: (name: string) => Promise<void>; collapsed: boolean; onToggle: () => void
}) {
  const tabs: { id: 'chats' | 'files' | 'artifacts'; icon: React.ReactNode; label: string; count: number }[] = [
    { id: 'chats', icon: <MessageCircle aria-hidden="true" size={16} strokeWidth={1.75} />, label: t('chat.chats'), count: chats.length },
    { id: 'files', icon: <FileText aria-hidden="true" size={16} strokeWidth={1.75} />, label: t('chat.files'), count: files.length },
    { id: 'artifacts', icon: <Archive aria-hidden="true" size={16} strokeWidth={1.75} />, label: t('chat.artifacts'), count: artifacts.length },
  ]
  const moveTab = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => { const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : -1; if (next >= 0) { event.preventDefault(); onTab(tabs[next].id); (event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role=tab]')[next])?.focus() } }
  return <div className={`cw-sidebar ${collapsed ? 'sessions-collapsed' : ''}`}>
    <div className="cw-sidebar-toggle"><button type="button" className="sidebar-collapse" aria-label={collapsed ? t('chat.expandChats') : t('chat.collapseChats')} title={collapsed ? t('chat.expandChats') : t('chat.collapseChats')} onClick={onToggle}>{collapsed ? <ChevronRight size={16} strokeWidth={1.75} /> : <ChevronLeft size={16} strokeWidth={1.75} />}</button></div>
    {!collapsed && <>
    <div className="p-space-3 pb-space-2">
      <Button variant="secondary" onClick={onNewChat} className="w-full justify-center" icon={<Plus aria-hidden="true" size={16} strokeWidth={1.75} />}>{t('chat.newChat')}</Button>
    </div>
    <div role="tablist" className="flex flex-col gap-[2px] px-space-2">
      {tabs.map((t, index) => <button key={t.id} id={`chat-sidebar-tab-${t.id}`} role="tab" aria-selected={tab === t.id} tabIndex={tab === t.id ? 0 : -1} onKeyDown={event => moveTab(event, index)} onClick={() => onTab(t.id)} className={`flex items-center justify-between rounded-[7px] px-space-2 py-space-2 text-label ${tab === t.id ? 'bg-hover font-semibold text-primary' : 'text-secondary hover:bg-hover'}`}>
        <span className="flex items-center gap-space-2"><span>{t.icon}</span>{t.label}</span><span className="text-caption text-muted">{t.count}</span>
      </button>)}
    </div>
    <div role="tabpanel" id="chat-sidebar-panel" aria-labelledby={`chat-sidebar-tab-${tab}`} className="min-h-0 flex-1 overflow-y-auto px-space-2 pb-space-3 pt-space-2">
      {tab === 'chats' && <>
        <SidebarHeading>{t('chat.chats')}</SidebarHeading>
        {chats.map(c => <button key={c.id} onClick={() => onSelectChat(c.id)} className={`mb-[2px] block w-full rounded-md px-space-2 py-space-2 text-left ${c.id === activeChatId ? 'bg-hover' : 'hover:bg-hover'}`}>
          <div className={`truncate text-label ${c.id === activeChatId ? 'font-semibold text-primary' : 'text-primary'}`}>{c.title}</div>
          <div className="truncate text-caption text-muted">{chatSubtitle(c)}</div>
        </button>)}
      </>}
      {tab === 'files' && <>
        <div className="flex items-center justify-between px-space-1 pb-space-2 pt-space-1"><SidebarHeading inline>{t('chat.files')}</SidebarHeading><button onClick={onUploadFile} className="text-caption font-semibold text-accent"><Plus aria-hidden="true" size={16} strokeWidth={1.75} className="inline" /> {t('chat.upload')}</button></div>
        {files.length === 0 ? <p className="px-space-1 py-space-2 text-caption text-muted">{t('chat.noFiles')}</p> : files.map(file => <div key={file.name} className="flex items-center gap-space-2 px-space-1 py-space-2"><a className="min-w-0 flex-1 truncate text-label text-primary hover:text-accent" href={`/api/chats/${encodeURIComponent(activeChatId)}/files/${encodeURIComponent(file.name)}`}>{file.name}</a><span className="text-caption text-muted">{file.size} B</span><button onClick={() => void onDeleteFile(file.name)} className="text-caption text-muted hover:text-error">{t('common.delete')}</button></div>)}
      </>}
      {tab === 'artifacts' && <>
        <SidebarHeading>{t('chat.artifacts')}</SidebarHeading>
        {artifacts.length === 0 && <p className="px-space-1 py-space-2 text-caption text-muted">{t('chat.artifactsEmpty')}</p>}
        {artifacts.map(({ m, index }) => { const s = artifactSummary(m.content); return <button key={index} onClick={() => onSelectArtifact(index)} className={`mb-[2px] block w-full rounded-md px-space-2 py-space-2 text-left ${index === activeArtifactIndex ? 'bg-hover' : 'hover:bg-hover'}`}>
          <div className="truncate text-label font-semibold text-primary">{s.title}</div>
          <div className="mt-[3px] flex items-center gap-space-2"><span className="rounded-full bg-accent-subtle px-space-2 py-[2px] text-caption font-semibold text-accent">{t('chat.draft')}</span><span className="text-caption text-muted">{t('chat.characters', { count: s.chars })}</span></div>
        </button> })}
      </>}
    </div></>}
  </div>
}
function SidebarHeading({ children, inline }: { children: React.ReactNode; inline?: boolean }) {
  return <div className={`text-section font-semibold uppercase tracking-section text-muted ${inline ? '' : 'px-space-1 pb-space-2 pt-space-1'}`}>{children}</div>
}

// ── Center: empty state, messages, composer ────────────────────────────────────
function EmptyState({ onCreate }: { onCreate: () => void }) {
  return <div className="flex h-full flex-col items-center justify-center p-space-8">
    <div className="w-full max-w-[520px] text-center">
      <div className="mb-space-2 text-[22px] font-bold text-primary">{t('chat.empty.title')}</div>
      <div className="mb-space-6 text-body text-secondary">{t('chat.empty.description')}</div>
      <div className="mb-space-6 flex justify-center"><Button variant="primary" onClick={onCreate}>{t('chat.createArtifact')}</Button></div>
    </div>
  </div>
}

function ThinkingDots() {
  return <div className="flex justify-start"><div className="flex gap-[4px] rounded-[12px] bg-surface px-space-3 py-space-3">{[0, 0.2, 0.4].map(d => <span key={d} className="h-[6px] w-[6px] rounded-full bg-muted" style={{ animation: `run-pulse 1.2s infinite ease-in-out ${d}s` }} />)}</div></div>
}

function SystemEvent({ text, onRetry }: { text: string; onRetry?: () => void }) {
  return <div className="cw-system-event"><span>{text}</span>{onRetry && <button type="button" aria-label={t('chat.retry')} title={t('chat.retry')} onClick={onRetry}><RotateCcw size={16} strokeWidth={1.75} /></button>}</div>
}

function MessageView({ message, last, onOpenArtifact, onRetry, onCopy, pinned, onPin, onUnpin }: {
  message: Message; last: boolean; onOpenArtifact: () => void; onRetry: () => void; onCopy: () => void; pinned: boolean; onPin: () => void; onUnpin: () => void
}) {
  const [showReasoning, setShowReasoning] = useState(false)
  const artifact = isArtifact(message); const summary = artifact ? artifactSummary(message.content) : null
  if (message.role === 'system') return <SystemEvent text={message.content} onRetry={last ? onRetry : undefined} />
  const mine = message.role === 'user'
  return <div className={`cw-message group flex ${mine ? 'justify-end' : 'justify-start'}`}>
    <div className={mine ? 'relative max-w-[70%]' : 'relative w-full'}>
      <div className={`whitespace-pre-wrap px-space-4 py-space-3 text-label leading-[1.6] ${mine ? 'rounded-[12px] bg-accent-subtle pr-12 text-primary' : 'cw-assistant-message text-secondary'}`}>
        {message.role === 'assistant' && !message.streaming && !artifact ? <Markdown source={message.content} /> : message.content || (message.streaming ? '…' : '')}
      </div>
      {artifact && summary && <button onClick={onOpenArtifact} className="mt-space-2 flex w-full max-w-[340px] items-center gap-space-3 rounded-[10px] border border-border-subtle bg-elevated px-space-3 py-space-3 text-left transition-colors hover:border-accent">
        <span className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[7px] bg-accent-subtle text-accent"><Archive aria-hidden="true" size={16} strokeWidth={1.75} /></span>
        <span className="min-w-0 flex-1"><span className="block truncate text-label font-semibold text-primary">{summary.title}</span><span className="block text-caption text-muted">{t('chat.characters', { count: summary.chars })} · {t('chat.items', { count: summary.items })}</span></span>
        <ArrowRight aria-hidden="true" size={16} strokeWidth={1.75} className="text-muted" />
      </button>}
      {message.reasoning && <><Button variant="ghost" size="sm" className="mt-space-1" onClick={() => setShowReasoning(v => !v)}>{showReasoning ? t('chat.hideReasoning') : t('chat.showReasoning')}</Button>{showReasoning && <div className="mt-space-1 whitespace-pre-wrap border-l border-border-subtle pl-space-2 font-mono text-caption text-muted">{message.reasoning}</div>}</>}
      {message.content && !message.streaming && <div className="cw-message-actions">
        <button type="button" aria-label={t('chat.copy')} title={t('chat.copy')} onClick={onCopy}><Clipboard size={16} strokeWidth={1.75} /></button>
        {message.role === 'assistant' && <><button type="button" aria-label={pinned ? t('chat.unpin') : t('chat.pin')} title={pinned ? t('chat.unpin') : t('chat.pin')} onClick={pinned ? onUnpin : onPin}>{pinned ? <PinOff size={16} strokeWidth={1.75} /> : <Pin size={16} strokeWidth={1.75} />}</button><button type="button" aria-label={t('chat.retry')} title={t('chat.retry')} onClick={onRetry}><RotateCcw size={16} strokeWidth={1.75} /></button></>}
      </div>}
    </div>
  </div>
}

function Composer({ value, onChange, onSubmit, onStop, streaming, placeholder, skillMatches, onPickSkill, onAttach, skills, onActivateSkill, activeSkills, onRemoveSkill, providerLabel }: {
  value: string; onChange: (v: string) => void; onSubmit: () => void; onStop: () => void; streaming: boolean; placeholder: string; skillMatches: string[]; onPickSkill: (name: string) => void; onAttach: () => void; skills: string[]; onActivateSkill: (name: string) => boolean; activeSkills: ActiveSkill[]; onRemoveSkill: (id: string) => void; providerLabel: string
}) {
  const textarea = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { if (textarea.current) { textarea.current.style.height = '0px'; textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 180)}px` } }, [value])
  return <div className="cw-composer p-space-4 pt-space-2">
    <div className="relative">
      {skillMatches.length > 0 && <div className="absolute bottom-full left-0 z-10 mb-space-1 w-full max-w-[280px] rounded-md border border-border-subtle bg-surface p-space-1">{skillMatches.map(name => <button key={name} onClick={() => onPickSkill(name)} className="block w-full rounded-sm px-space-2 py-space-1 text-left text-caption text-secondary hover:bg-hover">#{name}</button>)}</div>}
      <div className="rounded-[12px] border border-border-strong bg-surface p-space-2">
        {activeSkills.length > 0 && <div className="mb-space-2 flex flex-wrap gap-space-2">{activeSkills.map(skill => <Chip key={skill.id} onRemove={() => onRemoveSkill(skill.id)}>#{skill.id}</Chip>)}</div>}
        <div className="flex items-end gap-space-2 px-space-2">
          <textarea ref={textarea} aria-label={t('chat.enterMessage')} value={value} onChange={e => onChange(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSubmit() } }} placeholder={placeholder} rows={1} className="max-h-[180px] min-h-[52px] flex-1 resize-none overflow-y-auto border-none bg-transparent py-space-1 text-label text-primary outline-none placeholder:text-muted" />
          {streaming ? <button aria-label={t('chat.stop')} title={t('chat.stop')} onClick={onStop} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-error text-error"><Square size={16} strokeWidth={1.75} /></button> : <button aria-label={t('chat.send')} title={t('chat.send')} onClick={onSubmit} disabled={!value.trim()} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-accent text-app disabled:opacity-40"><Send size={16} strokeWidth={1.75} /></button>}
        </div>
        <div className="mt-space-1 flex items-center gap-space-1 border-t border-border-subtle pt-space-1">
          <IconButton icon={<Paperclip size={16} strokeWidth={1.75} />} aria-label={t('chat.attachFile')} title={t('chat.attachFile')} onClick={onAttach} className="!h-10 !w-10" />
          <Popover label={t('chat.skills')} aria-label={t('chat.selectSkill')} triggerClassName="!h-10 !px-space-2">{(close: () => void) => <div>{skills.map(name => <button key={name} type="button" onClick={() => { onActivateSkill(name); close() }} className="block w-full rounded-sm px-space-2 py-space-1 text-left text-caption text-primary hover:bg-hover">#{name}</button>)}</div>}</Popover>
          <span className="ml-auto truncate px-space-2 text-caption text-muted">{providerLabel}</span>
        </div>
      </div>
    </div>
  </div>
}

// ── Right: artifact panel ──────────────────────────────────────────────────────
function ArtifactEmpty({ onClose, onOpenLibrary, count }: { onClose: () => void; onOpenLibrary: () => void; count: number }) {
  return <div className="relative flex flex-1 flex-col items-center justify-center p-space-8 text-center">
    <IconButton data-artifact-close icon={<X size={16} strokeWidth={1.75} />} aria-label={t('common.close')} title={t('common.close')} className="absolute right-space-3 top-space-3 !h-10 !w-10" onClick={onClose} />
    <div className="mb-space-3 flex h-[44px] w-[44px] items-center justify-center rounded-[11px] bg-surface text-muted"><Archive aria-hidden="true" size={16} strokeWidth={1.75} /></div>
    <div className="mb-space-1 text-label font-semibold text-primary">{t('chat.noArtifactSelected')}</div>
    <div className="max-w-[220px] text-caption text-muted">{t('chat.artifactEmptyDescription')}</div>
    {count > 0 && <Button variant="secondary" size="sm" className="mt-space-4" onClick={onOpenLibrary}>{t('chat.openLibrary', { count })}</Button>}
  </div>
}

function ArtifactPanel({ message, comments, focused, onClose, onFocus, onPopout, onHistory, onExport, onCopy, onEditSection, onSelection, onResolveComment, onDeleteComment }: { message: Message; comments: ArtifactComment[]; focused: boolean; onClose: () => void; onFocus: () => void; onPopout: () => void; onHistory: () => void; onExport: () => void; onCopy: () => void; onEditSection: (heading: string, action: string) => void; onSelection: (text: string, action: string) => void; onResolveComment: (comment: ArtifactComment, resolved: boolean) => void; onDeleteComment: (comment: ArtifactComment) => void }) {
  const summary = artifactSummary(message.content)
  const sections = useMemo(() => splitSections(message.content), [message.content])
  const [selectedText, setSelectedText] = useState(''); const [selectionPoint, setSelectionPoint] = useState({ top: 0, left: 0 })
  const captureSelection = () => { const current = window.getSelection(); const text = current?.toString().trim() ?? ''; if (!text || !current?.rangeCount) { setSelectedText(''); return } const rect = current.getRangeAt(0).getBoundingClientRect(); setSelectedText(text); setSelectionPoint({ top: rect.bottom + 8, left: Math.max(8, rect.left) }) }
  return <>
    <div className="border-b border-border-subtle p-space-4">
      <div className="flex items-start justify-between gap-space-2">
        <div className="min-w-0 text-title font-bold text-primary">{summary.title}</div>
        <div className="flex shrink-0 gap-space-1">
          <button disabled className="rounded-md border border-border-subtle bg-elevated px-space-2 text-caption text-secondary">{t('chat.currentVersion')}</button>
           <IconButton icon={focused ? <ArrowLeft size={16} strokeWidth={1.75} /> : <ArrowRight size={16} strokeWidth={1.75} />} aria-label={focused ? t('chat.splitView') : t('chat.focus')} title={focused ? t('chat.splitView') : t('chat.focus')} className="!h-10 !w-10" onClick={onFocus} />
           <IconButton data-artifact-close icon={<X size={16} strokeWidth={1.75} />} aria-label={t('common.close')} title={t('common.close')} className="!h-10 !w-10" onClick={onClose} />
          <IconButton icon={<ExternalLink size={16} strokeWidth={1.75} />} aria-label={t('chat.popOut')} title={t('chat.popOut')} className="!h-10 !w-10" onClick={onPopout} />
          <IconButton icon={<History size={16} strokeWidth={1.75} />} aria-label={t('chat.versionHistory')} title={t('chat.versionHistory')} className="!h-10 !w-10" onClick={onHistory} />
          <IconButton icon={<Download size={16} strokeWidth={1.75} />} aria-label={t('chat.export')} title={t('chat.export')} className="!h-10 !w-10" onClick={onExport} />
          <IconButton icon={<Clipboard size={16} strokeWidth={1.75} />} aria-label={t('chat.copy')} title={t('chat.copy')} className="!h-10 !w-10" onClick={onCopy} />
        </div>
      </div>
      <div className="mt-space-2 flex flex-wrap items-center gap-space-2">
        <span className="rounded-full bg-accent-subtle px-space-2 py-[3px] text-caption font-semibold text-accent">{t('chat.draft')}</span>
        <span className="text-caption text-muted">{t('chat.documentVersion')}</span>
        <span className="text-caption text-muted">· {t('chat.items', { count: summary.items })}</span>
      </div>
    </div>
    <div className="relative min-h-0 flex-1 overflow-y-auto" onMouseUp={captureSelection}>
      {selectedText && <div className="fixed z-30 flex gap-1 rounded-md border border-border-strong bg-elevated p-1 shadow-lg" style={{ top: selectionPoint.top, left: selectionPoint.left }} onMouseDown={e => e.preventDefault()}>{selectionActionKeys.map(key => { const action = t(key); return <button key={key} onClick={() => { onSelection(selectedText, action); setSelectedText('') }} className="rounded-sm px-space-2 py-space-1 text-caption text-primary hover:bg-hover">{action}</button> })}</div>}
      {sections.map((sec, i) => <ArtifactSection key={i} heading={sec.heading} body={sec.body} onAction={action => onEditSection(sec.heading, action)} />)}
      {comments.length > 0 && <div className="border-t border-border-subtle p-space-4"><div className="mb-space-2 text-section font-semibold uppercase tracking-section text-muted">{t('chat.comments')}</div>{comments.map(comment => <div key={comment.id} className="mb-space-2 rounded-md border border-border-subtle bg-elevated p-space-3"><div className="truncate text-caption text-muted">“{comment.quoted_text}”</div><div className={`mt-space-1 text-label ${comment.resolved ? 'text-muted line-through' : 'text-primary'}`}>{comment.author}: {comment.body}</div><div className="mt-space-2 flex gap-space-2"><button onClick={() => onResolveComment(comment, !comment.resolved)} className="text-caption text-accent">{comment.resolved ? t('chat.reopen') : t('chat.resolved')}</button><button onClick={() => onDeleteComment(comment)} className="text-caption text-muted hover:text-error">{t('common.delete')}</button></div></div>)}</div>}
    </div>
  </>
}
const sectionActions = ['chat.action.rewrite', 'chat.action.shorten', 'chat.section.expand', 'chat.section.addExample', 'chat.section.changeTone'] as const
function ArtifactSection({ heading, body, onAction }: { heading: string; body: string; onAction: (action: string) => void }) {
  return <div className="border-b border-border-subtle p-space-4">
    <div className="mb-space-1 flex items-center justify-between">
      <div className="text-label font-bold text-primary">{heading}</div>
      <Popover align="end" label={<Ellipsis aria-hidden="true" size={16} strokeWidth={1.75} />} aria-label={t('chat.editSection', { heading })} triggerClassName="!h-10 !w-10 !px-0" className="w-[180px]">
        {(close: () => void) => <div>{sectionActions.map(key => { const action = t(key); return <button key={key} onClick={() => { onAction(action); close() }} className="block w-full rounded-sm px-space-2 py-space-1 text-left text-caption text-primary hover:bg-hover">{action}</button> })}</div>}
      </Popover>
    </div>
    <div className="whitespace-pre-wrap text-label text-secondary"><Markdown source={body} /></div>
  </div>
}
// Split an artifact into heading + body sections by markdown headings; the whole thing
// is one "Content" section if it has none.
function splitSections(content: string): { heading: string; body: string }[] {
  const lines = content.split('\n'); const out: { heading: string; body: string[] }[] = []
  for (const line of lines) {
    const h = line.match(/^#{1,3}\s+(.*)/)
    if (h) out.push({ heading: h[1].trim(), body: [] })
    else if (out.length) out[out.length - 1].body.push(line)
    else { out.push({ heading: t('chat.content'), body: [line] }) }
  }
  return out.map(s => ({ heading: s.heading, body: s.body.join('\n').trim() })).filter(s => s.heading || s.body)
}

// ── Context drawer ─────────────────────────────────────────────────────────────
function ContextDrawer({ context, onChange, tooLarge, estimate, onClose }: { context: SharedContextState; onChange: (c: SharedContextState) => void; tooLarge: boolean; estimate: number; onClose: () => void }) {
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [onClose])
  const toggleInstruction = (id: string) => onChange({ ...context, instructions: context.instructions.map(i => i.id === id ? { ...i, active: !i.active } : i) })
  return <>
    <div onClick={onClose} className="fixed inset-0 z-40 bg-black/40" />
    <aside role="dialog" aria-modal="true" aria-label={t('chat.manageContext')} className="fixed inset-y-0 right-0 z-50 flex w-[420px] max-w-[92vw] flex-col bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4">
        <div className="text-title font-bold text-primary">{t('chat.manageContext')}</div>
        <IconButton icon={<X size={16} strokeWidth={1.75} />} aria-label={t('common.close')} title={t('common.close')} className="!h-10 !w-10" onClick={onClose} />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-space-4">
        {tooLarge && <div className="mb-space-4 rounded-[9px] border border-error bg-error-subtle p-space-3"><div className="mb-space-1 text-caption font-semibold text-error">{t('chat.contextTooLarge')}</div><div className="text-caption text-error">{t('chat.contextTooLargeDescription')}</div></div>}
        <SidebarHeading>{t('chat.generalDescription')}</SidebarHeading>
        <Textarea value={context.text} onChange={e => onChange({ ...context, text: e.target.value })} placeholder={t('chat.contextDescriptionPlaceholder')} rows={4} className="resize-y text-body" aria-label={t('chat.contextDescription')} />
        <div className="mt-space-4"><SidebarHeading>{t('chat.pinnedMessages', { count: context.pinned.length })}</SidebarHeading></div>
        {context.pinned.length === 0 && <p className="text-caption text-muted">{t('chat.noPinnedMessages')}</p>}
        {context.pinned.map(item => <label key={item.id} className="flex items-center gap-space-2 py-space-2"><input type="checkbox" checked onChange={() => onChange({ ...context, pinned: context.pinned.filter(p => p.id !== item.id) })} className="h-[15px] w-[15px] shrink-0" /><span className="min-w-0 flex-1 truncate text-label text-primary">{item.content}</span></label>)}
        <div className="mt-space-4"><SidebarHeading>Files</SidebarHeading></div>
        <p className="text-caption text-muted">{t('chat.filesDescription')}</p>
        <div className="mt-space-4"><SidebarHeading>{t('chat.instructions')}</SidebarHeading></div>
        {context.instructions.map(i => <label key={i.id} className="flex items-center gap-space-2 py-space-2"><input type="checkbox" checked={i.active} onChange={() => toggleInstruction(i.id)} className="h-[15px] w-[15px] shrink-0" /><span className="text-label text-primary">{i.label}</span></label>)}
        <div className="mt-space-4 flex items-center justify-between rounded-[9px] bg-elevated p-space-3 text-caption text-secondary"><span>{t('chat.contextEstimate')}</span><b className={tooLarge ? 'text-error' : 'text-success'}>~{formatTokens(estimate)} token</b></div>
      </div>
      <div className="flex gap-space-2 border-t border-border-subtle p-space-4">
        <Button variant="secondary" className="flex-1 justify-center" onClick={() => onChange({ ...context, text: '', pinned: [] })}>{t('chat.clear')}</Button>
        <Button variant="primary" className="flex-1 justify-center" onClick={onClose}>{t('chat.apply')}</Button>
      </div>
    </aside>
  </>
}

function VersionHistoryModal({ message, onClose }: { message: Message; onClose: () => void }) {
  useEffect(() => { const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [onClose])
  const summary = artifactSummary(message.content)
  const [artifact, setArtifact] = useState<StoredArtifact | null>(null); const [selectedVersion, setSelectedVersion] = useState<string | null>(null); const [loadError, setLoadError] = useState(false)
  useEffect(() => { if (!message.artifactId) return; setArtifact(null); setSelectedVersion(null); setLoadError(false); void api<StoredArtifact>(`/api/artifacts/${encodeURIComponent(message.artifactId)}`).then(saved => { setArtifact(saved); setSelectedVersion(saved.versions.at(-1)?.version ?? null) }).catch(() => setLoadError(true)) }, [message.artifactId])
  const selected = artifact?.versions.find(version => version.version === selectedVersion)
  return <div onClick={onClose} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-space-4">
    <div role="dialog" aria-modal="true" onClick={e => e.stopPropagation()} className="flex h-[520px] max-h-[86vh] w-[880px] max-w-[92vw] flex-col overflow-hidden rounded-[14px] bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4"><div className="text-title font-bold text-primary">{t('chat.versionHistoryTitle', { title: summary.title })}</div><IconButton icon={<X size={16} strokeWidth={1.75} />} aria-label={t('common.close')} title={t('common.close')} className="!h-10 !w-10" onClick={onClose} /></div>
      <div className="flex min-h-0 flex-1">
        <div className="w-[280px] shrink-0 overflow-y-auto border-r border-border-subtle p-space-3">{artifact?.versions.slice().reverse().map(version => <button key={version.version} onClick={() => setSelectedVersion(version.version)} className={`mb-space-2 w-full rounded-[9px] p-space-3 text-left ${version.version === selectedVersion ? 'bg-hover' : 'hover:bg-hover'}`}><div className="flex items-center gap-space-2"><span className="text-label font-bold text-primary">{version.version}</span>{version.version === artifact.versions.at(-1)?.version && <span className="rounded-full bg-accent-subtle px-space-2 py-[1px] text-caption font-semibold text-accent">{t('chat.current')}</span>}</div><div className="mt-[3px] text-caption text-secondary">{new Date(version.created_at).toLocaleString('en-US')}</div></button>)}</div>
        <div className="min-h-0 flex-1 overflow-y-auto p-space-4">
          {!message.artifactId ? <div className="rounded-[9px] border border-border-subtle bg-elevated p-space-4 text-caption text-muted">{t('chat.versionUnavailable')}</div> : loadError ? <div className="rounded-[9px] border border-border-subtle bg-elevated p-space-4 text-caption text-muted">{t('chat.versionLoadFailed')}</div> : !artifact ? <div className="text-caption text-muted">{t('chat.versionLoading')}</div> : artifact.versions.length === 1 ? <div className="rounded-[9px] border border-border-subtle bg-elevated p-space-4 text-caption text-muted">{t('chat.onlyOneVersion')}</div> : selected ? <div><div className="mb-space-3 text-label font-semibold text-primary">{selected.version} · {new Date(selected.created_at).toLocaleString('en-US')}</div><div className="artifact-panel text-label"><Markdown source={selected.content} /></div></div> : null}
        </div>
      </div>
      <div className="flex justify-end border-t border-border-subtle p-space-4"><Button variant="secondary" onClick={onClose}>{t('common.close')}</Button></div>
    </div>
  </div>
}

// ── Export modal (markdown/text/json/html are real; PDF + share are stubs) ──────
const exportFormats = [{ id: 'markdown', label: t('chat.format.markdown') }, { id: 'text', label: t('chat.format.text') }, { id: 'json', label: t('chat.format.json') }, { id: 'html', label: t('chat.format.html') }]
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
  const download = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([render()], { type: mime })); a.download = `${summary.title.slice(0, 40) || 'artifact'}.${ext}`; a.click(); URL.revokeObjectURL(a.href); onToast(t('chat.downloaded')) }
  return <div onClick={onClose} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-space-4">
    <div role="dialog" aria-modal="true" onClick={e => e.stopPropagation()} className="w-[480px] max-w-[92vw] overflow-hidden rounded-[14px] bg-surface shadow-2xl">
      <div className="flex items-center justify-between border-b border-border-subtle p-space-4"><div className="text-title font-bold text-primary">{t('chat.exportArtifact')}</div><IconButton icon={<X size={16} strokeWidth={1.75} />} aria-label={t('common.close')} title={t('common.close')} className="!h-10 !w-10" onClick={onClose} /></div>
      <div className="max-h-[60vh] overflow-y-auto p-space-4">
        <div className="mb-space-4 text-label text-secondary">{summary.title} · document</div>
        <SidebarHeading>{t('chat.format')}</SidebarHeading>
        <div className="mb-space-4 grid grid-cols-2 gap-space-2">{exportFormats.map(f => <label key={f.id} className={`flex items-center gap-space-2 rounded-md border px-space-3 py-space-2 ${format === f.id ? 'border-accent bg-accent-subtle' : 'border-border-subtle'}`}><input type="radio" name="fmt" checked={format === f.id} onChange={() => setFormat(f.id)} className="h-[14px] w-[14px]" /><span className="text-caption text-primary">{f.label}</span></label>)}</div>
        <SidebarHeading>{t('chat.options')}</SidebarHeading>
        <label className="flex items-center gap-space-2 py-space-1"><input type="checkbox" checked={withTitle} onChange={() => setWithTitle(v => !v)} className="h-[15px] w-[15px]" /><span className="text-label text-primary">{t('chat.includeTitle')}</span></label>
        <div className="mt-space-4"><SidebarHeading>{t('chat.preview')}</SidebarHeading></div>
        <pre className="max-h-[120px] overflow-y-auto whitespace-pre-wrap rounded-md border border-border-subtle bg-elevated p-space-3 font-mono text-caption text-secondary">{render().slice(0, 600)}</pre>
      </div>
      <div className="flex gap-space-2 border-t border-border-subtle p-space-4">
        <Button variant="secondary" onClick={() => { void navigator.clipboard?.writeText(render()); onToast(t('chat.copied')) }}>{t('chat.copy')}</Button>
                <div className="flex-1" />
        <Button variant="primary" onClick={download}>{t('chat.download')}</Button>
      </div>
    </div>
  </div>
}
