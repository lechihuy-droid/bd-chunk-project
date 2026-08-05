import { t } from '../lib/i18n'
export type PagePhase = 'U1' | 'U2' | 'U3' | 'U4'
export default function PlaceholderPage({ eyebrow, title, phase }: { eyebrow: string; title: string; phase: PagePhase }) { return <div className="p-7"><div className="mb-2 text-[length:var(--hub-section-size)] font-semibold uppercase tracking-[var(--hub-section-tracking)] text-muted">{eyebrow}</div><h1 className="m-0 text-[24px] font-semibold text-primary">{title}</h1><p className="mt-2 text-secondary">{t('misc.placeholder.buildPhase', { phase })}</p></div> }
