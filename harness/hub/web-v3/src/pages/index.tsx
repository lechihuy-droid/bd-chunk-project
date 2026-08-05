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
import OverviewPage from './OverviewPage'
import HooksPage from './HooksPage'
import FilesPage from './FilesPage'
import ArtifactDetailPage from './ArtifactDetailPage'
import VgovReleasesPage from './VgovReleasesPage'
import VgovRunPage from './VgovRunPage'
import VgovOutputPage from './VgovOutputPage'
import VgovProvenancePage from './VgovProvenancePage'
import VgovComparePage from './VgovComparePage'

export const pages = [
  { path: 'overview', element: <OverviewPage /> },
  { path: 'chat', element: <ChatPage /> }, { path: 'sessions', element: <SessionsPage /> },
  { path: 'workflows', element: <WorkflowsPage /> }, { path: 'runs', element: <RunsPage /> },
  { path: 'artifacts', element: <ArtifactsPage /> },
  { path: 'artifacts/:artifactId', element: <ArtifactDetailPage /> },
  { path: 'agents', element: <AgentsPage /> }, { path: 'skills', element: <SkillsPage /> },
  { path: 'hooks', element: <HooksPage /> }, { path: 'files', element: <FilesPage /> },
  { path: 'approvals', element: <ApprovalsPage /> }, { path: 'usage', element: <UsagePage /> },
  { path: 'settings', element: <SettingsPage /> },
  { path: 'vgov/releases', element: <VgovReleasesPage /> },
  { path: 'vgov/run', element: <VgovRunPage /> },
  { path: 'vgov/output', element: <VgovOutputPage /> },
  { path: 'vgov/provenance', element: <VgovProvenancePage /> },
  { path: 'vgov/compare', element: <VgovComparePage /> },
]
