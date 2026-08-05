export type ProviderId = 'claude' | 'codex' | 'nvidia'

export const providerIds: ProviderId[] = ['claude', 'codex', 'nvidia']

export const asProviderId = (id: string): ProviderId =>
  id === 'claude' || id === 'codex' || id === 'nvidia' ? id : 'nvidia'

export const resolveProvider = (value: string, classes: Record<string, { provider: string }>) =>
  classes[value]?.provider ?? value
