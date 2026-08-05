import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { t } from '../lib/i18n'
import { Markdown } from '../lib/markdown'

type Artifact = { id: string; title: string; source: string; created_at: string; versions: { version: string; created_at: string; content: string }[] }

export default function ArtifactDetailPage() {
  const { artifactId = '' } = useParams()
  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { if (!artifactId) return; void api<Artifact>(`/api/artifacts/${encodeURIComponent(artifactId)}`).then(setArtifact).catch(() => setError(t('artifacts.detail.notFound'))) }, [artifactId])
  const version = artifact?.versions.at(-1)
  return <div className="mx-auto flex h-full max-w-[960px] flex-col gap-space-4 overflow-auto p-space-6"><div className="flex items-center justify-between"><Link to="/artifacts" className="inline-flex items-center gap-space-1 text-caption text-accent"><ArrowLeft size={16} strokeWidth={1.75} aria-hidden="true" />{t('artifacts.detail.back')}</Link><span className="text-caption text-muted">{artifact?.source ?? '—'}</span></div>{error ? <p className="text-error">{error}</p> : !artifact || !version ? <p className="text-secondary">{t('artifacts.detail.loading')}</p> : <article className="rounded-lg border border-border-subtle bg-surface"><header className="border-b border-border-subtle p-space-5"><h1 className="text-title font-bold text-primary">{artifact.title}</h1><p className="mt-space-1 text-caption text-muted">{version.version} · {version.created_at}</p></header><div className="p-space-5 text-label text-secondary"><Markdown source={version.content} /></div></article>}</div>
}
