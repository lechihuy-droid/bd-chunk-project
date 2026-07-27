# Detailed Design — Database Schema

> Superseded for local v1 by `../../design/D05_API_AND_STORAGE_CONTRACTS.md`.

**Document type:** Detailed Design  
**Version:** 0.1  
**Recommended:** PostgreSQL

## 1. Core tables

```text
workspaces
workflow_definitions
workflow_versions
workflow_runs
node_runs
node_attempts
agent_definitions
agent_versions
skill_definitions
skill_versions
artifacts
artifact_versions
review_requests
review_results
runtime_events
idempotency_keys
```

## 2. Key fields

### workflow_runs

```sql
id UUID PRIMARY KEY,
workflow_version_id UUID NOT NULL,
orchestrator_instance_id UUID,
status TEXT NOT NULL,
input_refs JSONB NOT NULL,
started_at TIMESTAMPTZ,
completed_at TIMESTAMPTZ
```

### node_attempts

```sql
id UUID PRIMARY KEY,
node_run_id UUID NOT NULL,
attempt_no INT NOT NULL,
execution_id TEXT,
status TEXT NOT NULL,
executor_type TEXT,
provider TEXT,
model TEXT,
usage_json JSONB,
error_json JSONB,
UNIQUE(node_run_id, attempt_no)
```

### artifact_versions

```sql
id UUID PRIMARY KEY,
artifact_id UUID NOT NULL,
version_no INT NOT NULL,
content_ref TEXT NOT NULL,
checksum TEXT NOT NULL,
metadata_json JSONB NOT NULL,
source_run_id UUID,
parent_version_id UUID,
UNIQUE(artifact_id, version_no)
```

## 3. Transaction rules

- State transition và runtime event append phải cùng transaction.
- Artifact version creation và update current version phải atomic.
- Idempotency key phải unique.
- Artifact Version content không được update.

## 4. Indexes

Index run status/date, node run status, execution ID, artifact workspace/status, artifact version order và runtime event sequence.
