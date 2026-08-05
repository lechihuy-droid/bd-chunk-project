import { useEffect, useState } from 'react'
import { Button, Input } from '../lib/ui'
import { vgov, type Release } from '../lib/vgovApi'

export default function VgovReleasesPage() {
  const [workflow, setWorkflow] = useState('rd-to-bd-api')
  const [releases, setReleases] = useState<Release[]>([])
  const [env, setEnv] = useState<Record<string, Release>>({})
  const [message, setMessage] = useState('')

  const load = () => {
    void vgov.releases(workflow).then(setReleases).catch(error => setMessage(String(error)))
    void vgov.environments(workflow).then(setEnv).catch(() => setEnv({}))
  }
  useEffect(load, [workflow])

  const promote = async (target: 'DEV' | 'PROD', release: Release) => {
    try {
      await vgov.setEnvironment(target, workflow, release.id, `${target} promotion from Hub`)
      setMessage(`${release.release_version} now points ${target}`)
      load()
    } catch (error) {
      setMessage(String(error))
    }
  }

  return (
    <div className="mx-auto max-w-[1100px] space-y-space-4 overflow-auto p-space-6">
      <div>
        <div className="text-section font-semibold uppercase tracking-section text-muted">Workflow delivery</div>
        <h1 className="text-title font-semibold text-primary">Release pointers</h1>
        <p className="mt-space-1 text-caption text-secondary">
          Publish then explicitly promote a workflow release. Technical manifest details stay with each output.
        </p>
      </div>
      <div className="flex max-w-md gap-space-2">
        <Input value={workflow} onChange={e => setWorkflow(e.target.value)} aria-label="Workflow ID" />
        <Button onClick={load}>Refresh</Button>
      </div>
      <div className="grid gap-space-3 md:grid-cols-2">
        {(['DEV', 'PROD'] as const).map(name => (
          <section key={name} className="rounded-lg border border-border-subtle bg-surface p-space-4">
            <div className="text-caption text-muted">{name} pointer</div>
            <div className="mt-space-1 text-label font-semibold text-primary">
              {env[name] ? `v${env[name].release_version}` : 'Not promoted'}
            </div>
          </section>
        ))}
      </div>
      {message && <p className="text-caption text-secondary">{message}</p>}
      <section className="overflow-hidden rounded-lg border border-border-subtle bg-surface">
        <div className="grid grid-cols-[1fr_auto_auto] gap-space-3 border-b border-border-subtle p-space-3 text-caption text-muted">
          <span>Release</span>
          <span>Status</span>
          <span>Actions</span>
        </div>
        {releases.map(release => (
          <ReleaseRow
            key={release.id}
            release={release}
            onPublish={() => void vgov.publish(release.id).then(load)}
            onPromote={target => void promote(target, release)}
          />
        ))}
      </section>
    </div>
  )
}

function ReleaseRow({ release, onPublish, onPromote }: { release: Release; onPublish: () => void; onPromote: (target: 'DEV' | 'PROD') => void }) {
  return (
    <div className="grid grid-cols-[1fr_auto_auto] items-center gap-space-3 border-b border-border-subtle p-space-3 last:border-0">
      <div>
        <div className="text-label font-semibold text-primary">v{release.release_version}</div>
        <div className="text-caption text-muted">{release.workflow_id}</div>
      </div>
      <span className="text-caption text-secondary">{release.status}</span>
      <div className="flex gap-space-2">
        {release.status === 'DRAFT' && <Button size="sm" onClick={onPublish}>Publish</Button>}
        {release.status === 'PUBLISHED' && (
          <>
            <Button size="sm" onClick={() => onPromote('DEV')}>Promote DEV</Button>
            <Button size="sm" onClick={() => onPromote('PROD')}>Promote / rollback PROD</Button>
          </>
        )}
      </div>
    </div>
  )
}
