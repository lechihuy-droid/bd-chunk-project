import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ApiError } from '../lib/api'
import { parseSse } from '../lib/sse'
import ArtifactRail from '../components/ArtifactRail'
import RunSpine, { type NodeView } from '../components/RunSpine'
import { getRun, getRunEvents, listRuns, listWorkflows, resumeGate, startRun, validateWorkflow, type IrNode, type RunEvent, type RunState, type Workflow } from '../lib/runsApi'
import { Button, Select, Textarea } from '../lib/ui'

type Interrupt = Record<string, unknown>
const initialNode = (node: IrNode): NodeView => ({ ...node, state: 'pending', output: '', reasoning: '' })
const metadata = (state: RunState | null) => state?.metadata ?? {}

export default function RunsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [workflowId, setWorkflowId] = useState('')
  const [objective, setObjective] = useState('')
  const [nodes, setNodes] = useState<NodeView[]>([])
  const [run, setRun] = useState<RunState | null>(null)
  const [events, setEvents] = useState<RunEvent[]>([])
  const [interrupt, setInterrupt] = useState<Interrupt | null>(null)
  const [recent, setRecent] = useState<RunState[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [resuming, setResuming] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const controller = useRef<AbortController | null>(null)

  useEffect(() => {
    void Promise.all([listWorkflows(), listRuns()]).then(([items, runs]) => {
      const hashQuery = window.location.hash.split('?')[1] ?? ''
      const requested = new URLSearchParams(hashQuery).get('wf') ?? ''
      setWorkflows(items); setWorkflowId(items.some(item => item.id === requested) ? requested : items[0]?.id ?? ''); setRecent(runs)
    }).catch(e => setError(e instanceof ApiError ? e.message : 'Không thể tải workflow'))
  }, [])

  useEffect(() => () => controller.current?.abort(), [])

  const applyState = useCallback((state: RunState) => {
    setRun(state)
    const meta = metadata(state); const done = new Set(Array.isArray(meta.completed_nodes) ? meta.completed_nodes.map(String) : [])
    const current = String(meta.current_node ?? ''); const nodeIndex = Number(meta.node_index); const outputs = meta.node_outputs && typeof meta.node_outputs === 'object' ? meta.node_outputs as Record<string, unknown> : {}
    setNodes(currentNodes => currentNodes.map((node, index) => ({ ...node, state: done.has(node.id) ? 'done' : (current === node.id || (!current && state.status === 'failed' && index === nodeIndex)) && state.status === 'failed' ? 'failed' : current === node.id && ['running', 'interrupted'].includes(state.status) ? 'running' : node.state === 'failed' ? 'failed' : 'pending', output: node.output || String(outputs[node.id] ?? '') })))
  }, [])

  const handleStream = useCallback(async (response: Response) => {
    if (!response.body) throw new Error('Run stream unavailable')
    for await (const item of parseSse(response.body)) {
      const data = item.data as Record<string, unknown>; const nodeId = typeof data.node === 'string' ? data.node : ''
      setEvents(current => [...current, { ...data, type: item.event, ts: new Date().toISOString() }])
      if (item.event === 'state_snapshot' && data.state && typeof data.state === 'object') applyState(data.state as RunState)
      if (item.event === 'assistant_delta' && nodeId) setNodes(current => current.map(n => n.id === nodeId ? { ...n, state: 'running', output: `${n.output}${String(data.text ?? '')}` } : n))
      if (item.event === 'reasoning' && nodeId) setNodes(current => current.map(n => n.id === nodeId ? { ...n, reasoning: `${n.reasoning}${String(data.text ?? '')}` } : n))
      if (item.event === 'artifact_written') { if (nodeId) setNodes(current => current.map(n => n.id === nodeId ? { ...n, artifact: true } : n)); setRefreshKey(key => key + 1) }
      if (item.event === 'interrupt') { setInterrupt(data); setRun(current => current ? { ...current, status: 'interrupted' } : current) }
      if (item.event === 'done') { setInterrupt(null); if (data.state && typeof data.state === 'object') applyState(data.state as RunState); else setRun(current => current ? { ...current, status: String(data.status ?? current.status) } : current) }
      if (item.event === 'error') {
        const message = String(data.message ?? 'Run thất bại')
        const failedState = data.state && typeof data.state === 'object' ? data.state as RunState : null
        if (failedState) applyState(failedState)
        setNodes(current => {
          const failedMeta = metadata(failedState); const nodeIndex = Number(failedMeta.node_index)
          const failedId = String(failedMeta.current_node ?? '') || (Number.isInteger(nodeIndex) ? current[nodeIndex]?.id ?? '' : '')
          return failedId ? current.map(node => node.id === failedId ? { ...node, state: 'failed', error: message } : node) : current
        })
        setError(message)
      }
    }
  }, [applyState])

  const launch = async () => {
    if (!workflowId || !objective.trim() || busy) return
    setError(''); setBusy(true); setRun(null); setEvents([]); setInterrupt(null); controller.current?.abort()
    const validation = await validateWorkflow(workflowId).catch(e => { setError(e instanceof ApiError ? e.message : 'Validate workflow thất bại'); return null })
    if (!validation?.ok || !validation.ir) { setError(validation?.errors.join('; ') || 'Workflow không hợp lệ'); setBusy(false); return }
    setNodes(validation.ir.sort((a, b) => a.order - b.order).map(initialNode))
    try { controller.current = new AbortController(); await handleStream(await startRun(workflowId, objective.trim(), controller.current.signal)) } catch (e) { if ((e as Error).name !== 'AbortError') setError((e as Error).message) }
    finally { setBusy(false); controller.current = null; void listRuns().then(setRecent).catch(() => undefined) }
  }

  const reopen = async (row: RunState) => {
    setError(''); setBusy(true)
    try { const detail = await getRun(row.run_id); const workflow = String(detail.metadata?.workflow_id ?? ''); const validation = workflow ? await validateWorkflow(workflow) : null; setNodes((validation?.ir ?? []).sort((a, b) => a.order - b.order).map(initialNode)); setRun(detail); setEvents(await getRunEvents(row.run_id)); applyState(detail); setInterrupt((detail.interrupts ?? []).find(item => item.status === 'pending') ?? null); setRefreshKey(key => key + 1) }
    catch (e) { setError(e instanceof ApiError ? e.message : 'Không thể mở lại run') } finally { setBusy(false) }
  }

  const gate = async (approved: boolean) => {
    if (!run || !interrupt || resuming) return
    setResuming(true); setError('')
    try { await handleStream(await resumeGate(run.run_id, String(interrupt.interrupt_id), approved)); setInterrupt(null) } catch (e) { setError((e as Error).message) } finally { setResuming(false) }
  }

  const label = (w: Workflow) => w.name ?? w.title ?? w.id
  return <div className="flex h-full min-h-0 flex-col gap-3 p-3 md:p-4">
    <form onSubmit={e => { e.preventDefault(); void launch() }} className="flex flex-wrap items-end gap-2 rounded-[var(--hub-radius-lg)] border border-border-subtle bg-surface p-3"><label className="flex min-w-[180px] flex-1 flex-col gap-1 text-[length:var(--hub-section-size)] font-semibold uppercase tracking-[var(--hub-section-tracking)] text-muted">Workflow<Select value={workflowId} onChange={e => setWorkflowId(e.target.value)}><option value="">Chọn workflow</option>{workflows.map(w => <option key={w.id} value={w.id}>{label(w)}</option>)}</Select></label><label className="flex min-w-[240px] flex-[2] flex-col gap-1 text-[length:var(--hub-section-size)] font-semibold uppercase tracking-[var(--hub-section-tracking)] text-muted">Mục tiêu<Textarea value={objective} onChange={e => setObjective(e.target.value)} rows={1} placeholder="Mục tiêu cho phiên chạy…" /></label><Button variant="primary" type="submit" disabled={busy || !workflowId || !objective.trim()}>{busy ? 'Đang chạy…' : 'Chạy'}</Button></form>
    {error && <div className="flex items-center gap-3 text-xs text-error">{error}<Button variant="ghost" size="sm" onClick={() => setError('')}>Ẩn</Button></div>}
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-border-subtle lg:flex-row"><div className="flex min-h-0 min-w-0 flex-1 flex-col"><div className="flex items-center justify-between border-b border-border-subtle bg-surface px-4 py-2"><span className="text-xs font-semibold">Spine</span><span className="font-mono text-[10px] text-muted">{run ? `${run.run_id} · ${run.status}` : 'chưa có run'}</span></div><RunSpine nodes={nodes} run={run} interrupt={interrupt} onGate={approved => void gate(approved)} resuming={resuming} /></div><ArtifactRail run={run} events={events} live={busy} refreshKey={refreshKey} /></div>
    {recent.length > 0 && <RecentRuns rows={recent} onChoose={row => void reopen(row)} disabled={busy} />}
  </div>
}

function RecentRuns({ rows, onChoose, disabled }: { rows: RunState[]; onChoose: (row: RunState) => void; disabled: boolean }) { const compact = useMemo(() => rows.slice(0, 5), [rows]); return <section className="rounded-[var(--hub-radius-lg)] border border-border-subtle bg-surface p-3"><div className="mb-2 text-[length:var(--hub-section-size)] font-semibold uppercase tracking-[var(--hub-section-tracking)] text-muted">Phiên chạy gần đây</div><div className="flex flex-wrap gap-2">{compact.map(row => <Button variant="secondary" size="sm" disabled={disabled} key={row.run_id} onClick={() => onChoose(row)} className="min-w-[180px] text-left"><span><span className="block truncate text-primary">{String(row.metadata?.objective ?? row.run_id)}</span><span className="font-mono text-[10px] text-secondary">{row.status} · {String(row.metadata?.updated_at ?? row.metadata?.created_at ?? '')}</span></span></Button>)}</div></section> }



