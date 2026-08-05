// UI copy for the usage area. Owned by one migration batch to keep parallel work conflict-free.
export const usage = {
  'usage.loadFailed': 'Unable to load usage data', 'usage.logLoadFailed': 'Unable to load activity log', 'usage.unpriced': 'unpriced', 'usage.priced': 'priced',
  'usage.section': 'MONITORING', 'usage.title': 'Usage & cost', 'usage.description': 'Inspect tokens, cache, and estimated cost over time.',
  'usage.today': 'Today', 'usage.sevenDays': '7 days', 'usage.thirtyDays': '30 days', 'usage.all': 'All', 'usage.filterSource': 'Filter source', 'usage.filterModel': 'Filter model', 'usage.allSources': 'All sources', 'usage.allModels': 'All models',
  'usage.tokens': 'Tokens', 'usage.calls': 'Calls', 'usage.cache': 'Cache', 'usage.loading': 'Loading…', 'usage.noData': 'No data available', 'usage.cacheRead': '{value} read', 'usage.cacheCreated': '{value} created',
  'usage.estimatedCost': 'Estimated cost', 'usage.estimateDisclaimer': 'Estimate — not actual spend', 'usage.pricingCoverageUnavailable': 'Pricing coverage: no data available', 'usage.pricingCoverage': '{priced} tokens priced · {unpriced} unpriced',
  'usage.dailyTrend': 'Daily trend', 'usage.estimateDollar': 'Estimate $', 'usage.byModel': 'By model', 'usage.byProvider': 'By provider', 'usage.model': 'Model', 'usage.source': 'Source', 'usage.cost': 'Cost', 'usage.quota': 'Quota', 'usage.offline': 'offline',
  'usage.log': 'Activity log', 'usage.logShowing': 'showing {shown}/{total}', 'usage.openToLoad': 'open to load', 'usage.time': 'Time', 'usage.session': 'Session', 'usage.command': 'Command', 'usage.openToLoadEvents': 'Open this section to load event logs matching the current filters.',
  'usage.tools': 'Tools', 'usage.suites': 'Suites', 'usage.inspect': 'Inspect',
} as const
