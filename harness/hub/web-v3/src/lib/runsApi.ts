import { api, apiRequest } from './api'

export type Workflow = { id: string; name?: string; title?: string; [key: string]: unknown }
export type IrNode = { id: string; order: number; gate?: string | null; prompt?: string; agent?: { id?: string; provider?: string; model?: string; [key: string]: unknown } | string }
export type RunState = { run_id: string; status: string; thread_id?: string; metadata?: Record<string, unknown>; interrupts?: Array<Record<string, unknown>>; [key: string]: unknown }
export type RunEvent = { ts?: string; type?: string; event?: string; node?: string; [key: string]: unknown }
export type Artifact = { name: string; chars: number }

export const listWorkflows = () => api<Workflow[]>('/api/workflows')
export const validateWorkflow = (target: string | { yaml_text: string }) => api<{ ok: boolean; errors: string[]; ir: IrNode[] | null }>('/api/workflows/validate', { method: 'POST', body: JSON.stringify(typeof target === 'string' ? { id: target } : target) })
export type RunInput = { kind: 'artifact'; id: string } | { kind: 'chat_file'; chat_id: string; name: string }
export const startRun = (id: string, objective: string, inputs: RunInput[] = [], signal?: AbortSignal) => apiRequest(`/api/workflows/${encodeURIComponent(id)}/runs`, { method: 'POST', body: JSON.stringify({ objective, inputs }), signal })
export const listRuns = () => api<RunState[]>('/api/agent/runs')
export const getRun = (id: string) => api<RunState>(`/api/agent/runs/${encodeURIComponent(id)}`)
export const getRunEvents = (id: string) => api<RunEvent[]>(`/api/agent/runs/${encodeURIComponent(id)}/events`)
export const listArtifacts = (runId: string) => api<{ artifacts: Artifact[] }>(`/api/workflows/runs/${encodeURIComponent(runId)}/artifacts`)
export const readArtifact = (runId: string, name: string) => api<{ name: string; text: string }>(`/api/workflows/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(name)}`)
export const resumeGate = (runId: string, interruptId: string, approved: boolean) => apiRequest(`/api/workflows/runs/${encodeURIComponent(runId)}/interrupts/${encodeURIComponent(interruptId)}/resume`, { method: 'POST', body: JSON.stringify({ action: approved ? 'resume' : 'reject' }) })
