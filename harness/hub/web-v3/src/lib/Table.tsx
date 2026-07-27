import type { ReactNode } from 'react'

export default function Table({ headers, children }: { headers: string[]; children: ReactNode }) {
  return <div className="overflow-x-auto rounded-lg border border-border-subtle"><table className="w-full border-collapse text-left text-xs"><thead className="bg-elevated text-[10px] uppercase tracking-wider text-muted"><tr>{headers.map(header => <th key={header} className="px-3 py-2 font-semibold">{header}</th>)}</tr></thead><tbody className="divide-y divide-border-subtle">{children}</tbody></table></div>
}


