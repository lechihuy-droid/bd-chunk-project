// UI copy for the settings area. Owned by one migration batch to keep parallel work conflict-free.
export const settings = {
  'settings.loadFailed': 'Unable to load settings', 'settings.invalidDays': 'Invalid number of days', 'settings.saveRetentionFailed': 'Unable to save retention period',
  'settings.section': 'SYSTEM', 'settings.title': 'Settings', 'settings.description': 'System information and retention period.', 'settings.providerHealth': 'Provider health', 'settings.version': 'Version', 'settings.details': 'Details',
  'settings.operationalRetention': 'Operational retention', 'settings.retentionDescription': 'Deletes event logs, job logs, and old session/usage caches. Audit records and artifacts are not deleted.', 'settings.days': 'Days', 'settings.daysAria': 'Retention days', 'settings.currentDays': 'Current: {days} days',
  'settings.modelCatalog': 'Model catalog', 'settings.default': 'default', 'settings.model': 'Model', 'settings.system': 'System', 'settings.root': 'Root', 'settings.runsDir': 'Runs directory', 'settings.port': 'Port',
} as const
