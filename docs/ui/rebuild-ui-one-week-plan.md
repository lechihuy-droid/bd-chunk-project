# Rebuild UI — One Week Implementation Plan

Status: Draft

Scope: BD Chunking / BD Harness UI planning

Purpose: Define a compressed one-week plan to rebuild the UI documentation and implementation specification for the BD-focused Harness project. The goal is not to build the full frontend in one week, but to produce a clear UI architecture, screen specification, component inventory, and AI-coding-ready implementation backlog.

---

## 1. Target Outcome

By the end of the week, the project should have a usable UI specification package for a BD Harness interface.

The UI should support:

- Project-based BD workflow management
- RD / QA / meeting-note ingestion visibility
- Traceable chunking status
- BD mapping and review workflow
- Agent execution visibility
- Human approval gates
- Artifact preview and export
- Future workflow builder integration

The expected output is a documentation-first UI foundation that Claude Code, Codex, Cursor, or a frontend engineer can implement from.

---

## 2. Four-Milestone Plan in One Week

```text
Milestone 1: Reverse Engineering & UI Foundation     Day 1-2
Milestone 2: Pattern Library & Design Language       Day 3-4
Milestone 3: Screen Specifications                   Day 5-6
Milestone 4: Component Inventory & Coding Backlog    Day 7
```

---

## 3. Milestone 1 — Reverse Engineering & UI Foundation

Timeline: Day 1-2

Goal: Decide what the BD Harness UI should learn from proven AI workspace, IDE, workflow, and productivity products.

### Reference Products

| Category | Products | What to learn |
|---|---|---|
| AI Workspace | ChatGPT, Claude, Gemini, DeerFlow, OpenHands | Chat, agent transparency, planner, tool calls, artifact interaction |
| IDE | Cursor, VS Code | Workspace layout, sidebar, tabs, editor-first interaction, file/artifact explorer |
| Productivity | Linear, Notion, Figma | Navigation, information architecture, inspector panel, clean state design |
| Workflow | LangGraph Studio, n8n, Flowise | Graph-based workflow builder, node/edge interaction, execution status |

### Deliverables

Create:

```text
docs/ui/00-ui-benchmark.md
docs/ui/01-design-principles.md
docs/ui/02-information-architecture.md
```

### Required Decisions

The first milestone should answer:

- Is the product closer to a chatbot, IDE, or workflow console?
- Which navigation model should be used?
- Should the main workspace be tab-based?
- Should the inspector be persistent?
- Should planner output be shown as tree, checklist, timeline, or graph?
- How much agent reasoning and tool execution should be visible?

### Recommended Decisions

For BD Harness:

- Use an IDE-like workspace, not a pure chatbot.
- Use left sidebar + central workspace + right inspector.
- Use tabs for artifacts and review documents.
- Use timeline for execution status.
- Use graph or structured task tree for planner view.
- Keep human approval as a first-class UI state.

---

## 4. Milestone 2 — Pattern Library & Design Language

Timeline: Day 3-4

Goal: Define reusable UI patterns before designing individual screens.

### Pattern Groups

Create:

```text
docs/ui/patterns/navigation.md
docs/ui/patterns/layout.md
docs/ui/patterns/workspace.md
docs/ui/patterns/chat.md
docs/ui/patterns/agent-execution.md
docs/ui/patterns/planner.md
docs/ui/patterns/workflow-graph.md
docs/ui/patterns/artifact-preview.md
docs/ui/patterns/review-gate.md
```

### Critical Patterns

#### Navigation Pattern

The UI should use:

- Primary sidebar
- Project switcher
- Global command palette
- Search
- Recent tasks
- Pinned artifacts

#### Workspace Pattern

The central area should support:

- Multi-tab workspace
- Split view
- Markdown preview
- JSON/YAML preview
- Excel-like table preview
- Diff/review mode

#### Inspector Pattern

The right panel should show context for the selected object:

- Source unit
- Chunk
- BD frame
- Agent step
- Tool call
- Artifact
- Review issue

#### Agent Execution Pattern

Agent activity should be represented with:

- Current agent
- Current task
- Status
- Tool calls
- Logs
- Intermediate artifacts
- Retry / cancel / approve actions

#### Review Gate Pattern

Human review must be visible as a state, not hidden as a backend rule.

Example states:

```text
Draft
Needs Review
Blocked
Approved
Rejected
Export Ready
```

---

## 5. Milestone 3 — Screen Specifications

Timeline: Day 5-6

Goal: Convert patterns into concrete screens.

### Core Screens

Create:

```text
docs/ui/screens/dashboard.md
docs/ui/screens/project-workspace.md
docs/ui/screens/ingestion.md
docs/ui/screens/chunking.md
docs/ui/screens/ontology-labeling.md
docs/ui/screens/bd-mapping.md
docs/ui/screens/planner.md
docs/ui/screens/agent-run.md
docs/ui/screens/artifact-review.md
docs/ui/screens/export.md
docs/ui/screens/settings.md
```

### Screen Template

Each screen should follow this structure:

```text
1. Purpose
2. User Entry Point
3. Primary User Goal
4. Layout Wireframe
5. Main Components
6. States
7. Interactions
8. Keyboard Shortcuts
9. Empty / Loading / Error States
10. Data Required
11. Future Extensions
```

### Priority Screens for the First UI Rebuild

The minimum useful UI should include:

1. Project Workspace
2. Ingestion
3. Chunking
4. BD Mapping
5. Artifact Review
6. Agent Run / Execution Timeline

---

## 6. Milestone 4 — Component Inventory & AI Coding Backlog

Timeline: Day 7

Goal: Turn the UI specification into an implementable backlog.

### Component Inventory

Create:

```text
docs/ui/components/component-inventory.md
docs/ui/components/ai-components.md
docs/ui/components/workspace-components.md
docs/ui/components/review-components.md
```

### Initial Component List

Foundation:

- Button
- Input
- Select
- Badge
- Tooltip
- Dialog
- Tabs
- Toast

Workspace:

- AppShell
- Sidebar
- TopBar
- StatusBar
- SplitPanel
- InspectorPanel
- WorkspaceTabs
- ArtifactPreview

BD Harness:

- ProjectCard
- SourceFileCard
- SourceUnitRow
- ChunkCard
- TraceabilityBadge
- OntologyLabelChip
- BDFrameCard
- MappingConfidenceBadge
- ReviewGateCard
- ExportPackageCard

AI / Agent:

- PromptComposer
- AgentCard
- ToolCallCard
- ExecutionTimeline
- PlannerTaskNode
- WorkflowNode
- CostUsageBadge
- ModelBadge

### AI Coding Backlog

Create issues or tasks in this order:

```text
1. Create AppShell layout
2. Create sidebar navigation
3. Create project workspace screen
4. Create ingestion screen
5. Create chunking screen
6. Create BD mapping screen
7. Create artifact review screen
8. Create execution timeline component
9. Create inspector panel
10. Create Storybook stories for core components
```

---

## 7. Recommended UI Architecture

```text
+-------------------------------------------------------------+
| TopBar: project switcher, command palette, model/status      |
+-------------------------------------------------------------+
| Sidebar | Main Workspace Tabs                         | Inspector |
|         |                                                |           |
|         | Project / Chunking / Mapping / Review         | Context   |
|         | Artifact Preview / Agent Run                  | Details   |
+-------------------------------------------------------------+
| StatusBar: current task, agent, token/cost, sandbox status   |
+-------------------------------------------------------------+
```

---

## 8. BD Harness Navigation Model

```text
Project
├── Overview
├── Sources
├── Chunking
├── Ontology
├── BD Mapping
├── Review
├── Artifacts
├── Agent Runs
└── Settings
```

The navigation should be project-centric because BD work is organized by delivery project, not by isolated chat sessions.

---

## 9. Key UX Principles

### Workspace First

The user should feel they are operating a BD production workspace, not chatting with a generic assistant.

### Traceability First

Every chunk, mapping, and BD output must show where it came from.

### Human Review First

No client-facing output should look final until approved.

### Agent Transparency

The UI must show what the AI is doing, which source it used, and what artifact it produced.

### Artifact First

The primary output is not a conversation. The primary output is a reviewable BD artifact.

---

## 10. UI Pattern Extractor Core

The UI rebuild should use `github.com/JCodesMore/ai-website-cloner-template` as the core engine for UI reverse engineering.

This repository should not be used as a direct cloning engine for the BD Harness UI. Its role is to provide the capture, analysis, and generation foundation for a higher-level **UI Pattern Extractor**.

### Reframed Purpose

Do not ask:

```text
How do we clone DeerFlow?
```

Ask instead:

```text
Which UI patterns from DeerFlow are worth adopting into Harness?
Where do those patterns fit in the BD Harness workflow?
Should they become part of our reusable UI Pattern Library?
```

### Target Pipeline

```text
URL / Screenshot / Public Repo
        ↓
AI Website Cloner Core
        ↓
DOM / Screenshot / Component Guess / Layout Guess
        ↓
UI Pattern Extractor
        ↓
Pattern Candidate
        ↓
Pattern Library
        ↓
UX Decision Record
        ↓
Harness UI Spec
        ↓
Storybook / Frontend Implementation
```

### Core Responsibilities

The cloner core should handle:

- Website capture
- Screenshot ingestion
- DOM extraction when available
- Layout reconstruction
- Initial component guess
- Visual hierarchy analysis
- HTML / React prototype generation when useful

The Harness-specific extractor layer should handle:

- Pattern naming
- Pattern classification
- Applicability scoring
- Fit-to-Harness analysis
- Comparison with existing patterns
- UX decision record generation
- Pattern library update
- Screen-spec update

### Pattern Extraction Output

Each cloned or analyzed product should produce a structured output:

```yaml
product: DeerFlow
source_type: website_or_repo_or_screenshot
analyzed_area: Planner UI

patterns:
  - name: Execution Timeline
    category: agent_execution
    evidence:
      - screenshot
      - dom_notes
      - interaction_notes
    strengths:
      - Shows task progress clearly
      - Makes long-running agent work understandable
    weaknesses:
      - May become noisy for simple tasks
    harness_fit:
      target_screen:
        - Agent Run
        - Planner
        - BD Mapping Review
      priority: high
      confidence: 0.85
    decision:
      action: adopt_with_modification
      reason: Useful for transparent BD generation and human review gates
```

### Pattern Library Update Rule

Every analyzed product should update one of these locations:

```text
docs/ui/patterns/
docs/ui/references/
docs/ui/decisions/
docs/ui/components/
docs/ui/screens/
```

The extractor should not generate final UI code directly unless the pattern has already been accepted into the library.

### Decision Matrix

For each pattern family, compare candidates from multiple products before adopting.

| Pattern Family | Candidate Products | Preferred Source | Reason |
|---|---|---|---|
| Sidebar | Linear, VS Code, Cursor | Linear + VS Code | Fast navigation with project/file hierarchy |
| Workspace | Cursor, VS Code, ChatGPT Canvas | Cursor | Strong multi-panel AI workbench model |
| Planner | DeerFlow, OpenHands, LangGraph Studio | DeerFlow + LangGraph Studio | Human-readable plan plus dependency-aware execution |
| Workflow Graph | LangGraph Studio, n8n, Flowise | LangGraph Studio | Clear graph semantics for agent flow |
| Inspector | Figma, Cursor, VS Code | Figma | Contextual properties panel is mature and scalable |
| Artifact Viewer | ChatGPT, VS Code, GitHub | VS Code + ChatGPT | Preview plus conversational handoff |
| Review Gate | GitHub PR, Azure DevOps, Linear | GitHub PR | Familiar approval and diff review workflow |
| Command Palette | VS Code, Cursor, Linear | VS Code | De facto keyboard-first interaction model |

### Definition of Done for the Extractor Layer

The cloner is successfully adapted when it can produce:

- Product analysis notes
- Pattern candidates
- Pattern fit score
- Evidence references
- Suggested Harness screen mapping
- UX decision record draft
- Component candidates
- Implementation notes for Storybook

The output should improve the Harness UI Design System over time. The goal is to build an original Harness design language from 10-20 analyzed products, not to create a copy of any single product.

---

## 11. Definition of Done for This One-Week UI Rebuild

The rebuild is done when the repository contains:

- UI benchmark document
- Design principles
- Information architecture
- Pattern library
- Screen specs for the core BD workflow
- Component inventory
- Initial implementation backlog
- Clear decision records for layout, planner, artifact viewer, and review gate
- Initial UI Pattern Extractor plan using `JCodesMore/ai-website-cloner-template` as the core engine

The week is not done if the output is only visual mockups without implementation-ready structure.

---

## 12. Next Implementation Step

After this documentation sprint, the recommended next step is:

```text
Build Storybook-first UI skeleton
```

Priority:

1. AppShell
2. Sidebar
3. WorkspaceTabs
4. InspectorPanel
5. Chunking screen
6. BD Mapping screen
7. Artifact Review screen
8. ExecutionTimeline
9. UI Pattern Extractor wrapper around the website cloner core

This keeps the UI independent from backend/runtime decisions while still making the product visible and testable early.
