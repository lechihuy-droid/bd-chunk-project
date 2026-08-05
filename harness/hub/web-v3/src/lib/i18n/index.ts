import { common } from './common'
import { chat } from './chat'
import { workflows } from './workflows'
import { usage } from './usage'
import { agents } from './agents'
import { skills } from './skills'
import { settings } from './settings'
import { approvals } from './approvals'
import { artifacts } from './artifacts'
import { runs } from './runs'
import { misc } from './misc'

// One flat English dictionary, assembled from per-area files so several
// migration batches can add keys without editing the same file.
export const en = { ...common, ...chat, ...workflows, ...usage, ...agents, ...skills, ...settings, ...approvals, ...artifacts, ...runs, ...misc } as const

export type TranslationKey = keyof typeof en

export function t(key: TranslationKey, vars?: Record<string, string | number>): string {
  const value = en[key] as string
  return vars ? value.replace(/\{(\w+)\}/g, (_, name: string) => String(vars[name] ?? `{${name}}`)) : value
}
