import { useEffect, useState } from 'react'
import { Button, Input, Select, Textarea } from '../lib/ui'
import { vgov, type Artifact, type Revision } from '../lib/vgovApi'
import { Markdown } from '../lib/markdown'

export default function VgovOutputPage() {
  const [project, setProject] = useState('demo-api')
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [artifactId, setArtifactId] = useState('')
  const [revisions, setRevisions] = useState<Revision[]>([])
  const [revisionId, setRevisionId] = useState('')
  const [content, setContent] = useState('')
  const [editing, setEditing] = useState(false)
  const [message, setMessage] = useState('')

  const loadArtifacts = () =>
    void vgov.artifacts(project).then(rows => {
      setArtifacts(rows)
      setArtifactId(current => current || rows[0]?.id || '')
    }).catch(e => setMessage(String(e)))
  useEffect(loadArtifacts, [project])

  useEffect(() => {
    if (!artifactId) return
    void vgov.revisions(artifactId).then(rows => {
      setRevisions(rows)
      setRevisionId(current => current || rows.at(-1)?.id || '')
    }).catch(e => setMessage(String(e)))
  }, [artifactId])

  useEffect(() => {
    if (revisionId) void vgov.content(revisionId).then(setContent).catch(e => setMessage(String(e)))
  }, [revisionId])

  const revise = async () => {
    try {
      const next = await vgov.edit(revisionId, content)
      setRevisions(rows => [...rows, next])
      setRevisionId(next.id)
      setEditing(false)
      setMessage(`Saved human revision ${next.revision_no}`)
    } catch (e) {
      setMessage(String(e))
    }
  }

  const approve = async () => {
    try {
      await vgov.approve(artifactId, revisionId)
      setMessage('Approved baseline updated')
    } catch (e) {
      setMessage(String(e))
    }
  }

  return (
    <div className="mx-auto max-w-[1100px] space-y-space-4 overflow-auto p-space-6">
      <div>
        <div className="text-section font-semibold uppercase tracking-section text-muted">Run → output → approve</div>
        <h1 className="text-title font-semibold text-primary">Output history</h1>
      </div>
      <div className="flex flex-wrap gap-space-2">
        <Input className="max-w-xs" value={project} onChange={e => setProject(e.target.value)} aria-label="Project ID" />
        <Button onClick={loadArtifacts}>Refresh</Button>
        <Select
          className="max-w-xs"
          value={artifactId}
          onChange={e => {
            setArtifactId(e.target.value)
            setRevisionId('')
          }}
        >
          {artifacts.map(a => (
            <option key={a.id} value={a.id}>{a.display_name || a.business_key}</option>
          ))}
        </Select>
        <Select className="max-w-xs" value={revisionId} onChange={e => setRevisionId(e.target.value)}>
          {revisions.map(r => (
            <option key={r.id} value={r.id}>Revision {r.revision_no} · {r.origin}</option>
          ))}
        </Select>
      </div>
      <div className="flex gap-space-2">
        <Button onClick={() => setEditing(value => !value)} disabled={!revisionId}>{editing ? 'Preview' : 'Edit content'}</Button>
        <Button variant="primary" onClick={() => void approve()} disabled={!revisionId}>Approve</Button>
      </div>
      {editing ? (
        <div className="space-y-space-2">
          <Textarea value={content} onChange={e => setContent(e.target.value)} aria-label="Revision markdown" className="min-h-[420px] font-mono" />
          <Button variant="primary" onClick={() => void revise()}>Save human edit</Button>
        </div>
      ) : (
        <article className="rounded-lg border border-border-subtle bg-surface p-space-5 text-label text-secondary">
          <Markdown source={content} />
        </article>
      )}
      {message && <p className="text-caption text-secondary">{message}</p>}
    </div>
  )
}
