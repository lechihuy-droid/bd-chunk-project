import { api } from './api'

const base = '/api/vgov'

export type Release = {
  id: string
  workflow_id: string
  release_version: string
  status: string
  git_commit?: string | null
  model_profile?: string
  model_name?: string
}

export type InputRevision = {
  id: string
  business_key: string
  revision_no: number
  content_hash: string
}

export type Run = {
  id: string
  status: string
  correlation_id: string
  error_code?: string | null
  completed_at?: string | null
}

export type Artifact = {
  id: string
  business_key: string
  display_name: string
  baseline?: { revision_id: string } | null
}

export type Revision = {
  id: string
  artifact_id: string
  revision_no: number
  origin: string
  content_hash: string
  parent_revision_id?: string | null
}

export type DiffRow = {
  category: string
  facet: string
  from?: string | boolean
  to?: string | boolean
  value?: string | boolean
}

export type Diff = {
  verdict: string
  changed: DiffRow[]
  unchanged: DiffRow[]
}

export type Lineage = {
  revision: Revision
  parent_chain: Revision[]
  run?: { id: string } | null
  manifest?: { manifest_hash: string; git_commit: string; input_hash: string } | null
  input_revision?: Revision | null
  workflow_release?: { workflow_id: string; release_version: string } | null
  components: { kind: string; ref: string; exact_version: string }[]
}

export const vgov = {
  releases: (workflowId?: string) =>
    api<Release[]>(`${base}/releases${workflowId ? `?workflow_id=${encodeURIComponent(workflowId)}` : ''}`),

  publish: (id: string) =>
    api<Release>(`${base}/releases/${id}/publish`, { method: 'POST' }),

  environments: (workflowId: string) =>
    api<Record<string, Release>>(`${base}/environments?workflow_id=${encodeURIComponent(workflowId)}`),

  setEnvironment: (environment: 'DEV' | 'PROD', workflow_id: string, release_id: string, reason: string) =>
    api(`${base}/environments/${environment}`, { method: 'PUT', body: JSON.stringify({ workflow_id, release_id, reason }) }),

  inputs: (projectKey: string) =>
    api<InputRevision[]>(`${base}/inputs?project_key=${encodeURIComponent(projectKey)}`),

  runs: (body: Record<string, string>) =>
    api<Run>(`${base}/runs`, { method: 'POST', body: JSON.stringify(body) }),

  run: (id: string) =>
    api<Run>(`${base}/runs/${id}`),

  artifacts: (projectKey: string) =>
    api<Artifact[]>(`${base}/artifacts?project_key=${encodeURIComponent(projectKey)}&artifact_type=API_BASIC_DESIGN`),

  revisions: (artifactId: string) =>
    api<Revision[]>(`${base}/artifacts/${artifactId}/revisions`),

  content: (revisionId: string) =>
    fetch(`${base}/revisions/${revisionId}/content`).then(async response => {
      if (!response.ok) throw new Error(`Request failed (${response.status})`)
      return response.text()
    }),

  edit: (revisionId: string, content: string) =>
    api<Revision>(`${base}/revisions/${revisionId}/edit`, { method: 'POST', body: JSON.stringify({ content }) }),

  approve: (artifact_id: string, revision_id: string) =>
    api(`${base}/baselines`, { method: 'POST', body: JSON.stringify({ artifact_id, revision_id }) }),

  lineage: (revisionId: string) =>
    api<Lineage>(`${base}/revisions/${revisionId}/lineage`),

  compare: (left: string, right: string) =>
    api<Diff>(`${base}/explain-difference`, { method: 'POST', body: JSON.stringify({ left: { revision_id: left }, right: { revision_id: right } }) }),
}
