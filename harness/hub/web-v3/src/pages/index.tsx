import ChatPage from './ChatPage'
import SessionsPage from './SessionsPage'
import RunsPage from './RunsPage'
import WorkflowsPage from './WorkflowsPage'
import AgentsPage from './AgentsPage'
import SkillsPage from './SkillsPage'
import ApprovalsPage from './ApprovalsPage'
import UsagePage from './UsagePage'
import SettingsPage from './SettingsPage'
import ArtifactsPage from './ArtifactsPage'

export const pages = [
  { path: 'chat', element: <ChatPage /> }, { path: 'sessions', element: <SessionsPage /> },
  { path: 'workflows', element: <WorkflowsPage /> }, { path: 'runs', element: <RunsPage /> },
  { path: 'artifacts', element: <ArtifactsPage /> },
  { path: 'agents', element: <AgentsPage /> }, { path: 'skills', element: <SkillsPage /> },
  { path: 'approvals', element: <ApprovalsPage /> }, { path: 'usage', element: <UsagePage /> },
  { path: 'settings', element: <SettingsPage /> },
]
