// UI copy for the runs area. Owned by one migration batch to keep parallel work conflict-free.
export const runs = {
  'runs.loadWorkflowsFailed': 'Unable to load workflows', 'runs.failed': 'Run failed', 'runs.validateFailed': 'Workflow validation failed', 'runs.invalidWorkflow': 'Workflow is invalid', 'runs.reopenFailed': 'Unable to reopen run', 'runs.workflow': 'Workflow', 'runs.selectWorkflow': 'Select workflow', 'runs.objective': 'Objective', 'runs.objectivePlaceholder': 'Objective for this run…', 'runs.running': 'Running…', 'runs.run': 'Run', 'runs.hideError': 'Hide', 'runs.spine': 'Spine', 'runs.noRun': 'No run yet', 'runs.recent': 'Recent runs',
  'runs.addInputs': 'Add inputs', 'runs.artifacts': 'Artifacts', 'runs.files': 'Files', 'runs.searchInputs': 'Search inputs…', 'runs.noArtifacts': 'No artifacts available.', 'runs.noFiles': 'No files available.', 'runs.inputArtifact': 'artifact', 'runs.inputFile': 'file', 'runs.removeInput': 'Remove input',
} as const
