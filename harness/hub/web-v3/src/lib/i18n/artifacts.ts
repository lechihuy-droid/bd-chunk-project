// UI copy for the artifacts area. Owned by one migration batch to keep parallel work conflict-free.
export const artifacts = {
  'artifacts.empty.title': 'No data yet', 'artifacts.empty.description': 'There is no data for this section.', 'artifacts.eyebrow': 'ORCHESTRATION',
  'artifacts.subtitle.online': 'Artifacts stored on the server. Syncing.', 'artifacts.subtitle.offline': 'Artifacts stored on the server. Using local cache.', 'artifacts.editInChat': 'Edit in Chat',
  'artifacts.search.placeholder': 'Search artifacts…', 'artifacts.search.label': 'Search artifacts', 'artifacts.empty.list': 'No artifacts yet.', 'artifacts.source.workflowRun': 'Workflow run',
  'artifacts.tab.output': 'Output', 'artifacts.tab.reviewIssues': 'Review Issues', 'artifacts.tab.references': 'References', 'artifacts.tab.versions': 'Versions', 'artifacts.current': 'current',
  'artifacts.meta.workflowName': 'Workflow name', 'artifacts.meta.runId': 'Run ID', 'artifacts.meta.createdBy': 'Created by', 'artifacts.meta.startedAt': 'Started at', 'artifacts.meta.completedAt': 'Completed at', 'artifacts.meta.duration': 'Duration',
  'artifacts.viewing': 'Viewing {version} · {date}', 'artifacts.detail.back': 'Artifacts', 'artifacts.detail.notFound': 'Artifact not found.', 'artifacts.detail.loading': 'Loading artifact…', 'artifacts.defaultTitle': 'Document',
} as const
