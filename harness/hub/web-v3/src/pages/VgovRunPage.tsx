import { useEffect, useState } from 'react'
import { Button, Input, Select } from '../lib/ui'
import { vgov, type InputRevision, type Release, type Run } from '../lib/vgovApi'

const terminal = new Set(['SUCCEEDED', 'FAILED', 'FAILED_PRECONDITION', 'CANCELLED'])

export default function VgovRunPage() {
  const [project, setProject] = useState('demo-api')
  const [workflow, setWorkflow] = useState('rd-to-bd-api')
  const [inputs, setInputs] = useState<InputRevision[]>([])
  const [input, setInput] = useState('')
  const [environment, setEnvironment] = useState('PROD')
  const [environmentRelease, setEnvironmentRelease] = useState<Release | null>(null)
  const [businessKey, setBusinessKey] = useState('F001')
  const [run, setRun] = useState<Run | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    void vgov.inputs(project).then(rows => {
      setInputs(rows)
      setInput(current => current || rows[0]?.id || '')
    }).catch(e => setError(String(e)))
  }, [project])

  useEffect(() => {
    void vgov.environments(workflow).then(rows => {
      setEnvironmentRelease(rows[environment] ?? null)
    }).catch(e => {
      setEnvironmentRelease(null)
      setError(String(e))
    })
  }, [environment, workflow])

  useEffect(() => {
    if (!run || terminal.has(run.status)) return
    const timer = window.setTimeout(() => void vgov.run(run.id).then(setRun).catch(e => setError(String(e))), 1000)
    return () => window.clearTimeout(timer)
  }, [run])

  const start = async () => {
    try {
      setError('')
      setRun(await vgov.runs({ project_key: project, workflow_id: workflow, input_revision_id: input, environment, output_business_key: businessKey }))
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div className="mx-auto max-w-[760px] space-y-space-4 overflow-auto p-space-6">
      <div>
        <div className="text-section font-semibold uppercase tracking-section text-muted">Project → workflow → run</div>
        <h1 className="text-title font-semibold text-primary">Run workflow</h1>
        <p className="mt-space-1 text-caption text-secondary">
          Choose imported RD, target environment, then name business output.
        </p>
      </div>
      <section className="rounded-lg border border-border-subtle bg-surface p-space-4">
        <div className="text-caption text-muted">Release đang chạy · {environment}</div>
        {environmentRelease ? (
          <>
            <div className="mt-space-1 text-label font-semibold text-primary">
              v{environmentRelease.release_version} · {environmentRelease.status}
            </div>
            <div className="mt-space-1 font-mono text-caption text-secondary">
              {environmentRelease.git_commit?.slice(0, 12) ?? 'Commit chưa được pin'}
            </div>
          </>
        ) : (
          <p className="mt-space-1 text-caption text-secondary">
            {environment} chưa trỏ tới release nào. Hãy promote một release đã publish trước khi chạy.
          </p>
        )}
        <a className="mt-space-3 inline-block text-caption text-accent hover:underline" href="#/vgov/releases">
          Quản lý release
        </a>
      </section>
      <div className="grid gap-space-3 rounded-lg border border-border-subtle bg-surface p-space-4">
        <label className="text-label text-secondary">
          Project
          <Input value={project} onChange={e => setProject(e.target.value)} />
        </label>
        <label className="text-label text-secondary">
          Workflow
          <Input value={workflow} onChange={e => setWorkflow(e.target.value)} />
        </label>
        <label className="text-label text-secondary">
          RD input
          <Select value={input} onChange={e => setInput(e.target.value)}>
            {inputs.map(row => (
              <option key={row.id} value={row.id}>{row.business_key} revision {row.revision_no}</option>
            ))}
          </Select>
        </label>
        <label className="text-label text-secondary">
          Environment
          <Select value={environment} onChange={e => setEnvironment(e.target.value)}>
            <option>DEV</option>
            <option>PROD</option>
          </Select>
        </label>
        <label className="text-label text-secondary">
          Output business key
          <Input value={businessKey} onChange={e => setBusinessKey(e.target.value)} placeholder="F001" />
        </label>
        <Button variant="primary" disabled={!input || !businessKey} onClick={() => void start()}>Run</Button>
      </div>
      {run && (
        <section className="rounded-lg border border-border-subtle bg-surface p-space-4">
          <div className="text-caption text-muted">Run {run.id}</div>
          <div className="mt-space-1 text-label font-semibold text-primary">{run.status}</div>
          {run.error_code && <div className="mt-space-1 text-caption text-error">{run.error_code}</div>}
        </section>
      )}
      {error && <p className="text-caption text-error">{error}</p>}
    </div>
  )
}
