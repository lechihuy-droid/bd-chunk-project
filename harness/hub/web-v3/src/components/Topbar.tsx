import { useLocation } from 'react-router-dom'
import { ProviderDot } from '../lib/ui'

const titles: Record<string, string> = { chat: 'Chat đa cửa sổ', sessions: 'Phiên đã lưu', workflows: 'Workflows', artifacts: 'Artifacts', runs: 'Runs', agents: 'Agents', skills: 'Skills', approvals: 'Chờ duyệt', usage: 'Usage & quota', settings: 'Cài đặt' }

export default function Topbar() {
  const page = useLocation().pathname.split('/')[1] || 'runs'
  const title = titles[page] ?? 'Runs'
  return <header className="flex items-center gap-[14px] border-b border-border-subtle bg-sidebar px-[18px] py-[10px]"><span className="text-[13px] text-secondary">{title} / <b className="font-semibold text-primary">Harness Hub</b></span><div className="ml-auto flex gap-2">
    {/* TODO(U4): wire /api/usage quota. */}
    <span className="flex items-center gap-[7px] rounded-full border border-border-subtle bg-elevated px-[10px] py-[3px] font-mono text-[11px] text-secondary"><ProviderDot provider="claude" />claude —</span><span className="flex items-center gap-[7px] rounded-full border border-border-subtle bg-elevated px-[10px] py-[3px] font-mono text-[11px] text-secondary"><ProviderDot provider="codex" />codex —</span><span className="flex items-center gap-[7px] rounded-full border border-border-subtle bg-elevated px-[10px] py-[3px] font-mono text-[11px] text-secondary"><ProviderDot provider="nvidia" />nvidia free</span>
  </div></header>
}


