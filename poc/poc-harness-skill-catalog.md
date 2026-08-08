# PoC Harness Skill Catalog

## Scope

This catalog defines the initial skill set for the BD Chunk PoC Harness, prioritizing web application delivery, backend/API work, data platforms, testing, security, and extensibility.

## Selected Skills

| # | Skill | Source | Primary Use | Priority |
|---|---|---|---|---|
| 1 | `backend-patterns` | ECC | Service layer, API, DB, cache patterns | P0 |
| 2 | `frontend-patterns` | ECC | React/Next.js frontend patterns | P0 |
| 3 | `api-design` | ECC | REST API contracts, pagination, errors | P0 |
| 4 | `postgres-patterns` | ECC | PostgreSQL schema/query/index optimization | P0 |
| 5 | `database-migrations` | ECC | Schema migration workflows | P0 |
| 6 | `clickhouse-io` | ECC | OLAP, analytics DB, data engineering | P0 Data |
| 7 | `frontend-app-builder` | OpenAI | Build production-oriented frontend/dashboard apps | P0 Web |
| 8 | `webapp-testing` | Anthropic | Browser-level web application testing | P0 Web |
| 9 | `e2e-testing` | ECC | Playwright E2E and test conventions | P0 |
| 10 | `data-visualization` | OpenAI | Charts, dashboards, data visualization | P0 Data |
| 11 | `analyze-data-quality` | OpenAI | Nulls, duplicates, drift, grain, joins, source disagreement | P1 Data |
| 12 | `jupyter-notebooks` | OpenAI | Reproducible SQL/Python analysis | P1 Data |
| 13 | `security-review` | ECC | Auth, input, secrets, security review | P1 |
| 14 | `tdd-workflow` | ECC | RED → GREEN → REFACTOR | P1 |
| 15 | `deployment-patterns` | ECC | Docker, CI/CD, health checks, rollback | P1 |
| 16 | `frontend-design` | Anthropic | Production-grade UI design and visual quality | P0 Web |
| 17 | `mcp-builder` | Anthropic | Build MCP servers and tool adapters | P1 Platform |
| 18 | `skill-creator` | Anthropic | Create and maintain reusable Harness skills | P1 Platform |
| 19 | `claude-api` | Anthropic | Claude API integration patterns | P1 Integration |
| 20 | `webapp-testing` (Anthropic canonical dependency) | Anthropic | Browser validation and functional web testing | P0 Web |

> Note: `webapp-testing` is intentionally treated as the canonical Anthropic browser-testing capability. If the runtime registry requires unique IDs by source, use `anthropic/webapp-testing`.

## Recommended Harness Grouping

```text
skills/
├── web/
│   ├── frontend-app-builder/       # OpenAI
│   ├── frontend-patterns/          # ECC
│   ├── frontend-design/            # Anthropic
│   ├── webapp-testing/             # Anthropic
│   └── e2e-testing/                # ECC
│
├── backend/
│   ├── backend-patterns/           # ECC
│   ├── api-design/                 # ECC
│   ├── security-review/            # ECC
│   └── claude-api/                 # Anthropic
│
├── data/
│   ├── postgres-patterns/          # ECC
│   ├── clickhouse-io/              # ECC
│   ├── database-migrations/        # ECC
│   ├── analyze-data-quality/       # OpenAI
│   ├── jupyter-notebooks/          # OpenAI
│   └── data-visualization/         # OpenAI
│
├── integration/
│   └── mcp-builder/                # Anthropic
│
├── engineering/
│   ├── tdd-workflow/               # ECC
│   └── deployment-patterns/        # ECC
│
└── meta/
    └── skill-creator/              # Anthropic
```

## Wave 1 — PoC Build Skills

Install/port these first:

1. `backend-patterns`
2. `frontend-patterns`
3. `api-design`
4. `postgres-patterns`
5. `database-migrations`
6. `frontend-app-builder`
7. `frontend-design`
8. `webapp-testing`
9. `e2e-testing`

This gives the Harness enough capability to build and validate a normal transactional web application.

## Wave 2 — Data Capability

Add after the application pipeline is stable:

1. `clickhouse-io`
2. `analyze-data-quality`
3. `jupyter-notebooks`
4. `data-visualization`

Target flow:

```text
PostgreSQL / ClickHouse
        ↓
Data Quality
        ↓
Notebook / Analysis
        ↓
Visualization / Dashboard
```

## Wave 3 — Platform Extensibility

Add:

1. `mcp-builder`
2. `skill-creator`
3. `claude-api`
4. `security-review`
5. `deployment-patterns`

Target flow:

```text
Capability missing?
      ↓
Skill Creator
      ↓
New Skill
      ↓
External system needed?
      ↓
MCP Builder
      ↓
Tool / MCP
      ↓
Skill Registry
      ↓
AgentManifest
```

## AgentManifest Mapping Examples

### Backend Engineer

```yaml
id: backend-engineer
skills:
  - backend-patterns
  - api-design
  - postgres-patterns
  - database-migrations
  - tdd-workflow
  - security-review
```

### Frontend Engineer

```yaml
id: frontend-engineer
skills:
  - frontend-app-builder
  - frontend-patterns
  - frontend-design
  - webapp-testing
  - e2e-testing
```

### Data Engineer

```yaml
id: data-engineer
skills:
  - postgres-patterns
  - clickhouse-io
  - database-migrations
  - analyze-data-quality
  - jupyter-notebooks
```

### Data Analyst

```yaml
id: data-analyst
skills:
  - analyze-data-quality
  - jupyter-notebooks
  - data-visualization
```

## License / Adoption Notes

- ECC is MIT-licensed and suitable as the primary OSS source for reusable Harness patterns.
- Anthropic skill licenses should be checked per skill before vendoring or redistributing them.
- Avoid assuming a public GitHub repository is OSS unless its license explicitly permits reuse.
- OpenAI skills should be referenced from the current plugin/role-specific skill repositories rather than relying on deprecated catalogs.

## PoC Decision

For the BD Chunk PoC, keep the number of agents small and expand capability primarily through skills. The initial recommendation is:

```text
Few stable agents
      +
Growing skill registry
      +
AgentManifest-based dynamic loading
```

This keeps orchestration manageable while allowing web, backend, and data capabilities to evolve independently.
