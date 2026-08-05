import { useState } from 'react'
import { Button, Input } from '../lib/ui'
import { vgov, type Diff } from '../lib/vgovApi'

const render = (value: unknown) => value === undefined ? '—' : String(value)

export default function VgovComparePage() {
  const [left, setLeft] = useState('')
  const [right, setRight] = useState('')
  const [diff, setDiff] = useState<Diff | null>(null)
  const [error, setError] = useState('')

  const compare = async () => {
    try {
      setError('')
      setDiff(await vgov.compare(left, right))
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div className="mx-auto max-w-[1100px] space-y-space-4 overflow-auto p-space-6">
      <div>
        <div className="text-section font-semibold uppercase tracking-section text-muted">Output → history / compare</div>
        <h1 className="text-title font-semibold text-primary">Explain difference</h1>
        <p className="mt-space-1 text-caption text-secondary">
          Compare two output revisions across all seven provenance categories.
        </p>
      </div>
      <div className="grid gap-space-2 md:grid-cols-[1fr_1fr_auto]">
        <Input value={left} onChange={e => setLeft(e.target.value)} placeholder="Left revision UUID" aria-label="Left revision UUID" />
        <Input value={right} onChange={e => setRight(e.target.value)} placeholder="Right revision UUID" aria-label="Right revision UUID" />
        <Button variant="primary" onClick={() => void compare()} disabled={!left || !right}>Compare</Button>
      </div>
      {diff && (
        <>
          <div className="text-label font-semibold text-primary">{diff.verdict}</div>
          <DiffTable title="Changed" rows={diff.changed} changed />
          <DiffTable title="Unchanged" rows={diff.unchanged} />
        </>
      )}
      {error && <p className="text-caption text-error">{error}</p>}
    </div>
  )
}

function DiffTable({ title, rows, changed = false }: { title: string; rows: Diff['changed']; changed?: boolean }) {
  return (
    <section className="overflow-hidden rounded-lg border border-border-subtle bg-surface">
      <h2 className={`border-b border-border-subtle p-space-3 text-label font-semibold ${changed ? 'text-warning' : 'text-secondary'}`}>
        {title}
      </h2>
      <div className="grid grid-cols-[140px_1fr_1fr] gap-space-2 p-space-3 text-caption text-muted">
        <span>Category</span>
        <span>{changed ? 'From' : 'Value'}</span>
        <span>{changed ? 'To' : 'Facet'}</span>
      </div>
      {rows.map((row, index) => (
        <div key={`${row.category}-${row.facet}-${index}`} className="grid grid-cols-[140px_1fr_1fr] gap-space-2 border-t border-border-subtle p-space-3 text-caption">
          <span className="font-semibold text-primary">{row.category}</span>
          <span className="break-all text-secondary">{changed ? render(row.from) : render(row.value)}</span>
          <span className="break-all text-secondary">{changed ? render(row.to) : row.facet}</span>
        </div>
      ))}
    </section>
  )
}
