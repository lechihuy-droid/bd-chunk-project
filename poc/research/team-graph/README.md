# Atlassian Teamwork Graph — Research Report

## Context Graph as Enterprise AI Infrastructure

**Research report — August 2026**

> Scope: Teamwork Graph only. AI-native SDLC is intentionally excluded and will be researched separately.

## Executive Summary

Atlassian Teamwork Graph (TWG) is best understood as an **enterprise context layer**, not merely a graph database or a variant of vector RAG.

Atlassian defines Teamwork Graph as a unified data layer that connects teamwork data from Jira, Confluence, and external systems such as Google Drive, Slack, GitHub, and other SaaS tools. Data from heterogeneous systems is normalized into a common object model, then connected through relationships, activity history, and permissions.

Primary source: https://developer.atlassian.com/platform/teamwork-graph/what-is-teamwork-graph/

By May 2026, Atlassian said Teamwork Graph contained more than **150 billion objects and relationships/connections**. Atlassian also reported an internal benchmark in which grounding agents with Teamwork Graph improved answer accuracy by about **44%** while reducing token usage by about **48%**. These are vendor-reported figures; Atlassian has not published enough benchmark methodology for independent validation.

Primary source: https://www.atlassian.com/blog/company-news/teamwork-graph-team-26

The strategic thesis is more important than the benchmark:

> **Model intelligence can become a commodity; organizational context cannot.**

Atlassian is therefore positioning itself to own the layer between enterprise systems of record and AI agents.

---

## 1. Research Scope

This report focuses on six questions:

1. What is Teamwork Graph?
2. How is heterogeneous enterprise data normalized into the graph?
3. How do relationships create operational context?
4. How is the graph kept fresh and permission-aware?
5. How do humans and agents access the graph?
6. How can a context graph create economic or strategic moat for enterprise AI?

Out of scope:

- Jira AI-native SDLC
- coding-agent workflow
- software-delivery agent orchestration
- application to a specific external enterprise architecture

---

## 2. Teamwork Graph is an Enterprise Context Layer

### Fact

Atlassian calls Teamwork Graph a **unified data layer** for teamwork data. It connects data from Jira, Confluence, Google Drive, Slack, GitHub, and additional SaaS or custom systems through connectors.

The graph uses a common data model for concepts such as work items, documents, messages, users, groups, projects, and many other object types.

Sources:

- https://developer.atlassian.com/platform/teamwork-graph/what-is-teamwork-graph/
- https://developer.atlassian.com/platform/teamwork-graph/twg-cli/

### Interpretation

A useful conceptual definition is:

```text
Teamwork Graph
=
semantic data model
+ entity normalization
+ relationships
+ activity history
+ permissions
+ continuous ingestion
+ query/traversal
+ agent interfaces
```

It should **not** be equated directly with a graph database product.

Atlassian exposes Cypher-style relationship traversal and GraphQL-based object retrieval, but this describes an access/query model, not the complete physical storage architecture.

Source:

- https://developer.atlassian.com/platform/teamwork-graph/graphql-and-cypher/

A more precise architectural label is:

> **Enterprise semantic/context layer**

---

## 3. Conceptual Architecture

```text
SOURCE SYSTEMS
Jira / Confluence / GitHub / Slack / Drive / Internal systems
                         │
                         ▼
                    CONNECTORS
        extraction / mapping / identity / ACL
                         │
                         ▼
                UNIFIED OBJECT MODEL
      Work item / Document / Message / PR / User...
                         │
                         ▼
                  RELATIONSHIP GRAPH
       canonical / activity / logical / inferred
                         │
                         ▼
                PERMISSION-AWARE CONTEXT
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Graph API   TWG CLI    Rovo MCP
              │          │          │
              └──────────┼──────────┘
                         ▼
                HUMAN + AI AGENTS
```

The essential transformation is:

```text
raw enterprise data
        ↓
normalized entities
        ↓
structured relationships
        ↓
permission-aware context
```

This reduces the amount of organizational structure an agent must reconstruct from scratch during every execution.

---

## 4. Common Object Model

### Fact

In Teamwork Graph, data items are represented as **objects**, and each object belongs to an **object type**.

Examples from Atlassian documentation include:

```text
Asana Task            → Work item
Google Calendar event → Calendar event
Figma file            → Design
```

The connector object model includes many categories such as:

- Work item
- Document
- Message
- Conversation
- Design
- Pull request
- Commit
- Build
- Deployment
- Repository
- Software service
- Test
- Test run
- Test plan
- Project

Sources:

- https://developer.atlassian.com/platform/teamwork-graph/object-types/
- https://developer.atlassian.com/platform/teamwork-graph/connector-reference/object-types-connectors/overview/

### Interpretation

Without normalization:

```text
Agent
 ├─ Jira schema
 ├─ GitHub schema
 ├─ Asana schema
 ├─ Slack schema
 └─ Drive schema
```

With a common semantic model:

```text
multiple source schemas
        ↓
normalized concepts
        ↓
agent reasoning
```

The agent can reason about a generic concept such as `Work Item` rather than repeatedly translating between `JiraIssue`, `GitHubIssue`, `AsanaTask`, and similar source-specific forms.

This common model is likely one contributor to reduced semantic and tool-use overhead.

---

## 5. Relationships Turn Data into Context

Atlassian distinguishes four major relationship categories.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/relationships/

### 5.1 Canonical relationships

These represent structural or source-of-truth relationships.

```text
Work Item
   └── belongs_to → Project

Pull Request
   └── in → Repository

Commit
   └── associated_with → Work Item
```

### 5.2 Activity relationships

These capture organizational behavior and history.

```text
User
 ├── created → Work Item
 ├── updated → Document
 ├── assigned → Issue
 └── viewed → Project
```

This introduces the temporal and behavioral dimension of enterprise context.

### 5.3 Logical relationships

Logical relationships abstract over source-specific structures.

An agent can ask conceptually for:

```text
all work items assigned to User A
```

without separately reasoning about every supported source-specific work-item type.

### 5.4 Inferred relationships

Inferred relationships may be derived from interaction patterns, metadata, behavior, or machine-learning inference.

Examples can include concepts such as:

```text
User A
 └── top_collaborator → User B
```

or inferred relevance between users and work items.

### Research implication

Canonical and inferred relationships have different epistemic status.

A mature context graph needs to preserve at least:

```text
relationship type
source
provenance
confidence
freshness
```

otherwise probabilistic context can be mistaken for authoritative organizational truth.

---

## 6. Context = Data + Relationship + History + Authority

A standalone document often answers:

```text
WHAT?
```

A context graph can potentially add:

```text
WHO?
WHY?
WHEN?
OWNED BY WHO?
RELATED TO WHAT?
CHANGED BY WHO?
DEPENDS ON WHAT?
WHO CAN SEE IT?
```

Atlassian explicitly argues that valuable context often lives in the relationships between artifacts, people, decisions, and prior activity rather than in one document or ticket alone.

Primary source:

- https://www.atlassian.com/blog/company-news/teamwork-graph-team-26

This leads to a useful distinction:

```text
Knowledge
= information about something

Context
= information + relationships + situation
```

---

## 7. Context Graph vs Vector RAG

Graph and RAG should not be treated as mutually exclusive.

Vector retrieval mainly asks:

```text
What content is semantically similar?
```

Graph traversal asks:

```text
How are these entities related?
```

For a question such as:

> Why was this feature changed?

vector search might return:

```text
Feature spec
Feature document
Related messages
Release notes
```

The model must still reconstruct the chain:

```text
Requirement
→ decision
→ ticket
→ PR
→ deployment
```

A graph can encode some of that chain explicitly:

```text
Requirement
   ↓ drives
Work Item
   ↓ implemented_by
Pull Request
   ↓ contains
Commit
   ↓ deployed_in
Deployment
```

Atlassian argues that pre-mapped context lets agents avoid discovering relationships one API call at a time.

Primary source:

- https://www.atlassian.com/blog/company-news/inside-rovo-mcp-usage

A realistic context architecture is therefore likely hybrid:

```text
graph traversal
+
semantic/vector retrieval
+
lexical search
+
metadata filters
```

---

## 8. Connectors are an Ontology and Semantic Integration Layer

### Fact

Atlassian says Teamwork Graph supports roughly **100 out-of-the-box connectors** and allows custom connectors using the Forge Teamwork Graph Connector SDK.

Connector responsibilities include:

- extracting source data;
- mapping data to Teamwork Graph object types;
- mapping users and groups;
- creating relationships;
- carrying permissions;
- participating in ingestion tasks and orchestration.

Sources:

- https://developer.atlassian.com/platform/teamwork-graph/what-is-teamwork-graph/
- https://developer.atlassian.com/platform/teamwork-graph/connector-reference/overview/

### Interpretation

A connector is not merely ETL.

Suppose three systems expose:

```text
Task
Issue
Request
```

The connector layer must determine whether these are:

```text
the same semantic type?
subtypes?
different objects?
relationships?
```

This is an **ontology mapping problem**.

Graph quality therefore depends heavily on semantic integration quality at the ingestion boundary.

---

## 9. Freshness is a First-Class System Problem

A context graph rapidly loses value if its state becomes stale.

Atlassian provides orchestration mechanisms for recurring ingestion, asynchronous execution, fan-out, retries, and long-running connector work.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/orchestration-concepts/

Conceptual flow:

```text
scheduled task
    ↓
scan source
    ↓
fan-out
    ↓
ingest updates
    ↓
report outcome
    ↓
retry failures
```

Connector requirements also distinguish synchronization behaviors such as append, upsert, and mirror, and recommend mirror-like synchronization where creation, update, and deletion in the source are reflected in the graph.

Source:

- https://developer.atlassian.com/platform/teamwork-graph/connector-requirements-and-best-practices/

A useful formulation is:

```text
graph quality
=
semantic quality
×
freshness
```

A semantically rich but stale graph can be actively harmful to autonomous agents.

---

## 10. Permission-Aware Context

### Fact

Teamwork Graph objects can carry ACLs describing who is allowed to view them.

ACL semantics can depend on users, groups, Atlassian workspaces, containers, and mapped external identities.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/permissions-and-access-control-lists/

Atlassian also documents a connector capability for permission replication and warns that data from connectors that do not replicate permissions can become broadly visible inside a workspace.

Source:

- https://developer.atlassian.com/platform/teamwork-graph/connector-requirements-and-best-practices/

### Interpretation

A context graph for agents cannot safely operate as:

```text
ingest everything
→ retrieve everything
→ filter afterward
```

because placing restricted information into an LLM context can itself create exposure.

Permission must participate in retrieval:

```text
query
→ permission-aware traversal
→ context assembly
→ model
```

This is a major distinction between a graph built for analytics and a graph used as an autonomous-agent context plane.

---

## 11. Relationships Have Temporal Semantics

Teamwork Graph relationship types can include time-to-live behavior.

Current Atlassian documentation shows examples where activity/logical relationships may have substantially shorter retention windows than canonical structural relationships.

Example source:

- https://developer.atlassian.com/platform/teamwork-graph/api-reference/relationship-types/atlassian-user-updated-documents/

This implies that the graph is not a timeless ontology. It has an operational lifecycle.

For example:

```text
User A updated Document X
```

may be highly useful recent context but not equally valuable forever.

By contrast:

```text
Document X belongs to Project Y
```

can remain structurally relevant for much longer.

A mature enterprise context model therefore needs to reason not only about relationship existence but also about recency and validity horizon.

---

## 12. Query Architecture: GraphQL + Cypher

Atlassian documents a combination of GraphQL and Cypher-oriented traversal.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/graphql-and-cypher/

Conceptually:

```text
Cypher
→ identify and traverse relationship patterns

GraphQL
→ retrieve strongly typed object fields
```

This creates a useful separation between:

```text
relationship discovery
≠
object projection
```

The public documentation still does not reveal the full internal ranking, query-planning, or context-assembly architecture.

---

## 13. Public API Maturity is Not the Same as Internal Platform Maturity

The direct Teamwork Graph API is still documented as an Early Access capability with important limitations.

Current restrictions include combinations of:

- Forge-only usage;
- test-organization constraints for many cases;
- marketplace/distribution limitations;
- possible breaking API changes;
- restricted production pathways.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/limitations-and-considerations/

This distinction matters:

```text
Atlassian internal Teamwork Graph maturity
≠
public programmable platform maturity
```

The internal context platform may be significantly more mature than what third-party developers can directly program against today.

---

## 14. Agent Access Surfaces

Atlassian currently exposes Teamwork Graph-related capability through multiple surfaces, including:

```text
Teamwork Graph API
TWG CLI
Rovo MCP
```

TWG CLI and Rovo MCP are described as complementary rather than interchangeable.

Primary source:

- https://support.atlassian.com/atlassian-rovo-mcp-server/docs/teamwork-graph-cli-and-rovo-mcp-decision-guide/

### TWG CLI

Designed for scenarios such as:

```text
terminal
CI/CD
shell workflows
local JSON/files
deep graph operations
```

### Rovo MCP

Better suited to:

```text
web LLMs
IDEs
sandboxes
MCP-native hosts
pre-declared tool interfaces
```

The key architectural distinction is:

```text
Graph
≠
MCP
≠
CLI
```

The graph is the context substrate. MCP and CLI are access surfaces.

---

## 15. Agent Skills are Another Layer

TWG CLI distributes agent skills for agent environments such as Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and systems using `.agents/skills` conventions.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/twg-cli/agents/skills/

This produces a useful four-layer distinction:

```text
GRAPH
What does the organization know?

TOOL
How can an agent access or change it?

SKILL
How should the agent use that tool correctly?

AGENT
Who reasons and executes?
```

Therefore:

```text
Graph ≠ Tool
Tool ≠ Skill
Skill ≠ Agent
```

This separation is important when studying agent architecture generally.

---

## 16. Read + Write Creates an Organizational-Memory Flywheel

If an agent only reads the graph:

```text
Graph
→ Agent
```

then the graph acts mainly as a context store.

Atlassian is increasingly emphasizing write behavior.

On July 1, 2026, Atlassian reported:

- more than **1 million monthly active MCP users**;
- more than **5 million MCP tool calls per workday**;
- nearly **one-third of tool calls were writes**.

Primary source:

- https://www.atlassian.com/blog/company-news/inside-rovo-mcp-usage

Writes can include behavior such as:

- creating Jira work items;
- updating status;
- recording decisions;
- linking work and conversations.

This produces a feedback loop:

```text
Graph
 ↓
Agent receives context
 ↓
Agent acts
 ↓
Structured work is created
 ↓
New relationships enter graph
 ↓
Future agents receive richer context
```

The graph therefore becomes closer to **organizational memory** than a passive knowledge repository.

---

## 17. Economic Thesis: Context Compression

Atlassian reports an internal result of approximately:

```text
+44% answer accuracy
-48% token usage
```

when agents are grounded with Teamwork Graph.

Primary source:

- https://www.atlassian.com/blog/company-news/teamwork-graph-team-26

Atlassian explains the broad mechanism as reduced need for an agent to discover cross-system relationships one API call at a time.

Related source:

- https://www.atlassian.com/blog/company-news/inside-rovo-mcp-usage

This suggests a useful research concept:

## Context Compression

```text
structured organizational context
        ↓
lower discovery overhead
        ↓
fewer tool calls / tokens
        ↓
higher first-pass accuracy
```

If this generalizes, context architecture becomes an **AI economics and FinOps lever**, not just a retrieval optimization.

---

## 18. Evidence Quality of the 44% / 48% Claims

Atlassian has not publicly disclosed enough benchmark detail to establish universal validity.

Missing or insufficiently documented details include:

- benchmark dataset;
- number and distribution of tasks;
- baseline retrieval architecture;
- model configuration;
- graph maturity;
- definition of accuracy;
- token accounting;
- confidence intervals;
- workload characteristics.

The appropriate evidence assessment is:

```text
Claim exists in primary sources:
HIGH confidence

Generalizability:
LOW–MEDIUM confidence

Independent validation:
NOT YET
```

The defensible statement is:

> Atlassian has internal evidence that pre-structured organizational context can materially reduce inference/retrieval overhead and improve answer quality in its evaluated workloads.

It is not defensible to state that graph grounding universally reduces token usage by 48%.

---

## 19. Mercedes-Benz Case

Atlassian describes Mercedes-Benz building custom Forge connectors for specialist engineering systems such as:

- defect management;
- requirements traceability;
- release workflows.

The resulting graph links concepts such as:

```text
defect
→ requirement
→ test case

component
→ vehicle model

engineering discussion
→ decision
```

Atlassian reports outcomes including:

- 90% improvement in defect intake quality;
- 85% faster duplicate detection;
- 10× faster software delivery.

Primary source:

- https://www.atlassian.com/blog/company-news/teamwork-graph-team-26

These are vendor/customer-reported case-study metrics, not independently controlled evidence.

The important architectural observation is that Teamwork Graph is designed to ingest **domain-specific enterprise objects**, not only generic office SaaS data.

---

## 20. Moat Thesis

Mike Cannon-Brookes summarized the strategic formula as:

```text
Acceleration = Context × Intelligence
```

Primary source:

- https://www.atlassian.com/blog/company-news/founder-update-team-26

The strategic argument is that frontier intelligence can increasingly be purchased as a service, while the accumulated context of how a particular organization operates is much harder to reproduce.

Potential sources of moat include:

### 20.1 Accumulated organizational history

```text
years of:
tickets
decisions
documents
code
collaboration
activity
```

### 20.2 Relationship density

Graph value may depend more on:

```text
number
× quality
× freshness
of relationships
```

than on raw object count.

### 20.3 Write-back flywheel

Agent activity generates more structured organizational memory.

### 20.4 Permission-aware integration

Context has enterprise value only if it can be consumed without breaking security boundaries.

---

## 21. Switching Cost May Live in Relationships, Not Raw Data

Migrating a document repository can often be approximated as:

```text
copy files
```

Migrating an enterprise context graph is harder:

```text
copy objects
+
copy ontology
+
copy relationships
+
copy identities
+
copy permissions
+
copy history
+
copy inferred signals
+
preserve semantics
```

This suggests that the most defensible potential switching cost is not ownership of raw files but the accumulated **network of organizational relationships**.

This is an analytical hypothesis, not a proven Atlassian metric.

---

## 22. Risk: False Context

Graph structure can make a relationship appear authoritative even when it is stale or probabilistic.

Relationships can be:

```text
stale
incorrect
missing
duplicated
conflicting
wrongly inferred
```

A context graph used by agents therefore needs to preserve and expose concepts such as:

```text
provenance
relationship type
confidence
freshness
source
last updated
```

The canonical-vs-inferred distinction in Atlassian's relationship model is particularly important here.

Primary source:

- https://developer.atlassian.com/platform/teamwork-graph/relationships/

---

## 23. Context Explosion Still Exists

A graph containing 150B+ objects and relationships obviously cannot be inserted directly into an LLM context window.

Graph technology does not remove the retrieval problem. It changes it.

From:

```text
Which documents are similar?
```

to:

```text
Which subgraph is minimally sufficient for this task?
```

This still requires mechanisms such as:

```text
query planning
ranking
traversal depth
relationship weighting
scope control
summarization
```

The detailed retrieval, ranking, and context-assembly layer appears to be one of the least publicly documented parts of Teamwork Graph and is therefore a priority research gap.

---

## 24. More Tools Do Not Necessarily Produce Better Agents

Atlassian notes that TWG CLI and Rovo MCP overlap in capability and recommends choosing an appropriate primary surface for a given runtime and workflow.

Primary source:

- https://support.atlassian.com/atlassian-rovo-mcp-server/docs/teamwork-graph-cli-and-rovo-mcp-decision-guide/

A broader implication is:

```text
more tools
→ larger decision space
→ more planning ambiguity
→ more chances of wrong tool choice
```

TWG CLI changelogs also emphasize compact, agent-friendly output and skills intended to reduce follow-up inspection turns.

Source:

- https://developer.atlassian.com/platform/teamwork-graph/twg-cli/changelog/

Tool discoverability and output compactness are therefore part of agent economics, not merely developer ergonomics.

---

## 25. Teamwork Graph as a "System of Context"

Traditional enterprise software often provides systems of record:

```text
CRM    = system of record for customers
ERP    = system of record for transactions
Jira   = system of record for work
GitHub = system of record for code
```

A useful interpretation of Teamwork Graph is a new layer:

```text
System of Context
```

This is not an official Atlassian product category in this exact wording.

A system of context does not need to own all source records. Instead it owns or coordinates:

```text
semantic normalization
+
relationships
+
cross-system context
+
permission-aware access
```

That may be strategically more relevant to AI agents than any single underlying system of record.

---

## 26. Architecture Synthesis

```text
┌─────────────────────────────────────┐
│ 7. AGENTS / HUMAN EXPERIENCES       │
│ Claude, Codex, Cursor, Rovo, Humans │
├─────────────────────────────────────┤
│ 6. SKILLS / AGENT SEMANTICS         │
│ product + workflow instructions     │
├─────────────────────────────────────┤
│ 5. ACCESS SURFACES                  │
│ MCP / TWG CLI / Graph API           │
├─────────────────────────────────────┤
│ 4. QUERY & CONTEXT SELECTION        │
│ GraphQL / Cypher / search / ranking │
├─────────────────────────────────────┤
│ 3. TEAMWORK GRAPH                   │
│ objects + relationships + history   │
├─────────────────────────────────────┤
│ 2. IDENTITY / PERMISSIONS / SYNC    │
│ ACL + freshness + provenance        │
├─────────────────────────────────────┤
│ 1. SOURCE SYSTEMS                   │
│ Jira / GitHub / Slack / Drive /...  │
└─────────────────────────────────────┘
```

Connectors connect source systems upward into the graph.

Agent actions can write back into source systems and create new graph context, producing a closed-loop organizational-memory system.

---

## 27. Confirmed vs Unknown

### Relatively well confirmed

Atlassian documentation clearly supports:

- common object model;
- standardized object types;
- canonical/activity/logical/inferred relationships;
- connectors;
- permissions and ACL propagation;
- mirror/incremental synchronization concepts;
- GraphQL/Cypher interfaces;
- MCP/CLI access surfaces;
- agent skills;
- public API limitations.

### Partially confirmed

Atlassian reports:

- +44% answer accuracy;
- -48% token usage;
- 5M+ MCP calls per workday;
- nearly one-third writes.

Usage telemetry is relatively credible as first-party system data. Performance claims require much more methodology.

### Largely unknown

The following remain insufficiently public:

- physical graph storage architecture;
- entity-resolution algorithms;
- duplicate reconciliation;
- graph ranking;
- relationship weighting;
- context assembly;
- graph + vector-search interaction;
- inferred-link confidence scoring;
- graph QA;
- total graph-maintenance economics;
- detailed benchmark methodology.

These should be the next research targets.

---

## 28. Research Hypotheses

### H1 — Context Graph reduces reasoning cost

Pre-structured relationships reduce the work a model must perform to reconstruct organizational context.

### H2 — Relationship quality matters more than raw object volume

A smaller graph with accurate, fresh relationships may be more valuable than a huge but sparse or stale graph.

### H3 — Permission-aware context is a prerequisite for enterprise agents

Shared context cannot safely become agent infrastructure if authorization does not travel with objects and relationships.

### H4 — Write-back creates a compounding moat

More agent use can create richer structured memory, improving future context and reinforcing adoption.

### H5 — Context portability may be more strategically valuable than model ownership

Models can change while enterprise context persists.

### H6 — Ontology and entity resolution are likely hidden hard problems

The difficult problem is not storing a graph. It is turning heterogeneous enterprise systems into one coherent semantic network.

---

## 29. Research Questions for Part II

### Data model

- How does Atlassian manage schema evolution?
- Which object types are fixed versus extensible?
- How much custom domain ontology is supported?

### Entity resolution

- How is one person represented consistently across Slack, GitHub, Jira, and other systems?
- How are duplicate projects and artifacts reconciled?
- What happens when two source systems disagree?

### Relationship creation

- What proportion of relationships are canonical versus inferred?
- How are inferred relationships generated?
- Is confidence stored or exposed?

### Retrieval

- How do graph traversal and vector/semantic search interact?
- How is traversal depth selected?
- Are relationships ranked or weighted?
- How is minimal sufficient context assembled for an agent?

### Economics

- Which workloads produced the reported 48% token reduction?
- Do savings come from fewer calls, smaller context, or less reasoning?
- What is the graph-maintenance cost relative to inference savings?

### Governance

- How are permissions propagated through inferred relationships?
- How are agent-created writes governed?
- Can incorrect writes or relationships be rolled back and versioned?

### Portability

- Can customers export their graph?
- Can graph semantics be migrated to another vendor?
- Who effectively owns ontology, relationship history, and inferred context?

The portability questions are especially important for distinguishing **moat** from **lock-in**.

---

## 30. Research Conclusion

Teamwork Graph represents a more ambitious enterprise-AI architecture than simply adding vector RAG to a document repository.

It attempts to transform:

```text
enterprise information
```

into:

```text
enterprise context
```

through:

```text
normalization
+
relationships
+
history
+
permissions
+
continuous synchronization
```

and then expose that context to multiple AI agents through interfaces that are not tied to one model.

The core thesis can be reduced to:

```text
LLM
provides generic intelligence.

Teamwork Graph
provides organizational understanding.
```

If frontier intelligence continues to commoditize, organizational context may become one of the most durable AI assets inside an enterprise.

The key research question is therefore not:

> Should enterprises use a graph database?

but:

> **How can heterogeneous organizational activity be transformed into a fresh, permission-aware, machine-legible network of entities and relationships that agents can reason over with lower cost and higher reliability?**

That is the deeper intellectual problem behind Teamwork Graph.

---

# Primary Source Pack

## P0 — Core architecture

1. **What is Teamwork Graph — Atlassian Developer**  
   https://developer.atlassian.com/platform/teamwork-graph/what-is-teamwork-graph/

2. **Object Types — Atlassian Developer**  
   https://developer.atlassian.com/platform/teamwork-graph/object-types/

3. **Relationships — Atlassian Developer**  
   https://developer.atlassian.com/platform/teamwork-graph/relationships/

4. **Permissions and ACL — Atlassian Developer**  
   https://developer.atlassian.com/platform/teamwork-graph/permissions-and-access-control-lists/

5. **GraphQL and Cypher — Atlassian Developer**  
   https://developer.atlassian.com/platform/teamwork-graph/graphql-and-cypher/

## P0 — Ingestion and maintenance

6. **Connector Requirements and Best Practices**  
   https://developer.atlassian.com/platform/teamwork-graph/connector-requirements-and-best-practices/

7. **Orchestration Concepts**  
   https://developer.atlassian.com/platform/teamwork-graph/orchestration-concepts/

## P1 — Agent access

8. **Teamwork Graph CLI**  
   https://developer.atlassian.com/platform/teamwork-graph/twg-cli/

9. **TWG CLI vs Rovo MCP Decision Guide**  
   https://support.atlassian.com/atlassian-rovo-mcp-server/docs/teamwork-graph-cli-and-rovo-mcp-decision-guide/

10. **Agent Skills**  
    https://developer.atlassian.com/platform/teamwork-graph/twg-cli/agents/skills/

## P1 — Strategy and economics

11. **Teamwork Graph: The Context Engine Behind Your AI**  
    https://www.atlassian.com/blog/company-news/teamwork-graph-team-26

12. **What 5M+ Daily MCP Tool Calls Taught Us**  
    https://www.atlassian.com/blog/company-news/inside-rovo-mcp-usage

13. **Mike Cannon-Brookes — Team '26 Founder Update**  
    https://www.atlassian.com/blog/company-news/founder-update-team-26

---

## Source Confidence

- **Architecture facts:** High — Atlassian developer documentation is concrete and internally consistent.
- **Usage telemetry:** High–Medium — first-party telemetry, not externally audited.
- **Performance claims (+44% / -48%):** Medium — repeated in primary sources, but benchmark methodology is incomplete.
- **Strategic moat interpretation:** Analytical hypothesis — synthesis in this report, not a fact proven by Atlassian.

---

## Next Research Module

**Teamwork Graph Part II — Ontology, Entity Resolution and Retrieval Architecture**

Recommended order:

```text
ontology
→ entity resolution
→ relationship quality
→ retrieval / traversal
→ graph + vector search
→ context assembly
→ evaluation
```

AI-native SDLC should remain a separate subsequent report.
