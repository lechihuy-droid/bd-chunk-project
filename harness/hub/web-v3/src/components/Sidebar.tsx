import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { BarChart3, Bot, FileText, Folder, GitCompare, History, LayoutDashboard, MessagesSquare, PanelLeftClose, PanelLeftOpen, Play, Settings, ShieldCheck, Sparkles, Webhook, Workflow } from 'lucide-react'
import { api } from '../lib/api'
import { t } from '../lib/i18n'
import { Status } from '../lib/ui'

const zones = [
  { label: t('nav.zone.overview'), items: [[LayoutDashboard, t('nav.overview'), '/overview']] },
  { label: t('nav.zone.chat'), items: [[MessagesSquare, t('nav.chat'), '/chat'], [History, t('nav.sessions'), '/sessions']] },
  { label: t('nav.zone.orchestration'), items: [[Workflow, t('nav.workflows'), '/workflows'], [FileText, t('nav.artifacts'), '/artifacts'], [Play, t('nav.runs'), '/runs'], [Bot, t('nav.agents'), '/agents'], [Sparkles, t('nav.skills'), '/skills'], [Webhook, t('nav.hooks'), '/hooks'], [Folder, t('nav.files'), '/files']] },
  { label: 'Version Governance', items: [[Play, 'Run workflow', '/vgov/run'], [FileText, 'Output history', '/vgov/output'], [History, 'Provenance', '/vgov/provenance'], [GitCompare, 'Compare outputs', '/vgov/compare']] },
  { label: t('nav.zone.monitoring'), items: [[ShieldCheck, t('nav.approvals'), '/approvals'], [BarChart3, t('nav.usage'), '/usage']] },
  { label: t('nav.zone.system'), items: [[Settings, t('nav.settings'), '/settings']] },
] as const

type Artifact = { id: string; title: string }
const recentArtifacts = (): Artifact[] => { try { const cached = JSON.parse(localStorage.getItem('hub-v3-artifacts') ?? 'null'); if (Array.isArray(cached)) return cached.slice(-5).reverse(); const chats = JSON.parse(localStorage.getItem('hub-v3-chats') ?? '[]') as { messages?: { role: string; content: string; streaming?: boolean }[] }[]; return chats.flatMap(chat => (chat.messages ?? []).filter(message => message.role === 'assistant' && !message.streaming && message.content.length >= 1200).map((message, index) => ({ id: `${index}:${message.content.slice(0, 20)}`, title: message.content.split('\n').find(Boolean)?.slice(0, 60) || t('nav.untitledArtifact') }))).slice(-5).reverse() } catch { return [] } }
const link = 'nav-item flex w-full items-center gap-[9px] rounded-[var(--hub-radius-md)] px-[10px] py-[7px] text-left text-secondary no-underline hover:bg-elevated hover:text-primary'

export default function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const [recent, setRecent] = useState<Artifact[]>(recentArtifacts)
  const [providers, setProviders] = useState<{ available: boolean }[] | null>(null)
  useEffect(() => { void api<{ available: boolean }[]>('/api/providers').then(setProviders).catch(() => setProviders(null)); void api<{ artifacts: Artifact[] }>('/api/artifacts').then(data => { localStorage.setItem('hub-v3-artifacts', JSON.stringify(data.artifacts)); setRecent(data.artifacts.slice(-5).reverse()) }).catch(() => undefined) }, [])
  const count = providers?.filter(provider => provider.available).length
  // Width comes from the .app grid track (240px, or 48px when collapsed); a fixed
  // width here overflows the track and paints over the page while collapsed.
  return <aside className="flex w-full min-w-0 flex-col gap-0 overflow-y-auto border-r border-border-subtle bg-sidebar px-[10px] py-[14px]">
    <div className="flex items-center gap-[10px] px-[10px] pb-4 pt-2"><div className="grid h-[34px] w-[34px] shrink-0 place-items-center rounded-[var(--hub-radius-lg)] bg-[var(--hub-accent)] font-bold text-app">H</div><div className="sidebar-label"><div className="font-semibold">Harness Hub</div><Status kind="ready" label={count === undefined ? t('common.notAvailable') : t('common.onlineProviders', { count, provider: count === 1 ? 'provider' : 'providers' })} /></div><button type="button" className="sidebar-collapse ml-auto" aria-label={collapsed ? t('nav.expand') : t('nav.collapse')} title={collapsed ? t('nav.expand') : t('nav.collapse')} onClick={onToggle}>{collapsed ? <PanelLeftOpen size={16} strokeWidth={1.75} aria-hidden="true" /> : <PanelLeftClose size={16} strokeWidth={1.75} aria-hidden="true" />}</button></div>
    {zones.map(zone => <div key={zone.label}><div className="sidebar-zone px-[10px] pb-[5px] pt-[14px] text-section font-semibold uppercase tracking-section text-muted">{zone.label}</div>{zone.items.map(([Icon, label, to]) => <NavLink key={to} to={to} className={link} title={label} aria-label={label}><Icon size={18} strokeWidth={1.75} aria-hidden="true" /><span className="sidebar-label">{label}</span></NavLink>)}</div>)}
    {recent.length > 0 && <div className="sidebar-label"><div className="px-[10px] pb-[5px] pt-[14px] text-section font-semibold uppercase tracking-section text-muted">{t('nav.recent')}</div>{recent.map(item => <NavLink key={item.id} to="/artifacts" className={`${link} block truncate`} title={item.title}>{item.title}</NavLink>)}</div>}
    <div className="sidebar-footer mt-auto border-t border-border-subtle px-[10px] pb-1 pt-3 text-[11px] text-muted">Hub v3 · localhost:8799</div>
  </aside>
}
