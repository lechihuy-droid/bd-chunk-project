# D07 — Deployment, SLO and Operations

```yaml
document_id: HH-DES-D07
version: 1.1
status: In Review
owner: Platform
depends_on: [D01, D05, D06]
research_sources: [HH-RES-R03, HH-RES-R04, HH-RES-R07]
```

## 1. Supported topology v1

```text
Windows/local host
  FastAPI/Uvicorn, one process
    in-process services/runtime/gateway
    local provider subprocesses
    local runtime/config/cache files
    outbound HTTPS to approved model APIs
  Browser on loopback
```

Start bằng project run script; không yêu cầu database, broker, Docker hay CDN. Cache là disposable; runtime/config/artifact là durable local data.

## 2. Environment

| Environment | Data/provider | Mục đích |
|---|---|---|
| test | tmp dirs + fake provider | deterministic CI/local tests |
| dev | local fixtures, optional real provider | development |
| local-v1 | operator data + approved provider | supported use |

Production/shared-host là unsupported trước Gate E.

## 3. Configuration

- Paths, provider catalog, risk tier và caps có một source trong `config.py`/versioned config.
- Secret chỉ từ environment; startup báo thiếu secret khi route cần nó, không dump value.
- Config thay đổi security boundary cần restart và audit.
- Validate writable roots, runtime directory và provider executable ở startup.

## 4. Initial engineering objectives

Đây là target cần owner đo/chốt, không phải production SLA:

| Signal | Target local v1 |
|---|---|
| Health endpoint | p95 < 200 ms |
| Cached list/dashboard API | p95 < 1 s |
| Workflow create/start overhead trước provider | p95 < 500 ms |
| Persisted event → SSE delivery | p95 < 1 s |
| Cancel observed by Runtime | < 2 s; CLI hard-kill theo grace config |
| Restart recovery scan | < 10 s cho 1,000 local runs |
| Runtime state loss | Chỉ theo durability envelope đã pass R03 probes; chưa claim power-loss zero-loss |
| Active workflow runs | default cap 4, configurable after load test |
| SSE clients | default cap 20 |
| Artifact/output | explicit per-run/file caps; reject before disk exhaustion |

Provider latency/availability tách khỏi Hub SLO nhưng phải đo.

## 5. Observability

Structured log fields:

`timestamp`, `level`, `component`, `correlation_id`, `run_id`, `node_id`, `execution_id`, `event`, `duration_ms`, `status`, `error_code`.

Metrics:

- request count/latency/error;
- active runs/executions/SSE;
- run/attempt outcome và duration;
- provider TTFT/duration/error/retry/token/cost;
- interrupt age;
- event append/replay errors;
- artifact bytes/scan/quarantine;
- CLI process timeout/cancel/orphan;
- cache hit/reparse duration.

Không label metric bằng prompt, user content hoặc unbounded ID nếu backend metric không chịu được cardinality.

## 6. Alert conditions

Local UI/log warning tối thiểu:

- runtime JSON/event corruption;
- repeated provider auth/policy failure;
- process survives hard kill;
- disk remaining dưới configured threshold;
- interrupt quá tuổi;
- event sequence gap;
- artifact hash mismatch;
- startup path/security validation fail.

## 7. Backup và restore

Backup set:

- workflows, agents, policy/risk config;
- runtime threads/runs/events/checkpoints;
- artifact manifests/content;
- audit evidence.

Exclude: cache, temporary execution dirs, raw secret files.

Restore test:

1. stop server;
2. restore into empty validated root;
3. verify hashes/path ownership;
4. startup recovery scan;
5. replay sampled run;
6. verify artifact hash;
7. do not auto-resume lost execution.

Initial recovery objectives cần OD-05/RD-02 chốt. Trước khi R03 power-loss probes pass, chỉ claim process-crash recovery cho committed transaction journal; không claim RPO = last completed replace/atomic write. RTO đề xuất < 30 phút manual restore.

## 8. Release

- Run full backend tests và frontend build/check applicable.
- Migration script required khi persisted schema thay đổi.
- Backup trước migration; migration idempotent hoặc có rollback.
- Release notes liệt kê contract/schema/version/security changes.
- Không deploy multi-worker khi file runtime mutation còn single-process.

## 9. Capacity và degradation

- Reject new run khi active-run/disk/provider quota cap đạt; existing run được cancel/read.
- Telemetry/cache failure không được làm mất execution result; báo degraded.
- Provider unavailable không làm API health giả down toàn bộ.
- Artifact scan unavailable: quarantine, không fail-open.
- Runtime store unavailable/corrupt: stop mutation, read-only diagnostics nếu an toàn.

## 10. Evolution topology

Chỉ Gate E mới xem xét: authenticated edge, multiple API replicas, database, broker/outbox, object storage, isolated remote CLI worker, centralized telemetry và HA/DR. Không copy SLO local sang distributed architecture.

Controlled Windows executor là deployment subsystem riêng, không nằm trong FastAPI adapter hardening. Nếu triển khai cần installation/upgrade/rollback cho Job supervisor, restricted identity, workspace storage boundary và privileged egress provisioning/broker; Hub process phải tiếp tục non-elevated.

## 11. Acceptance

- Startup validate topology/config.
- Single-process constraint enforced.
- Logs correlation end-to-end và redaction pass.
- Cancel/recovery/disk-low/degraded paths test được.
- Backup restore drill replay được state/artifact mẫu.
- Durability/RPO claim trace được tới exact OS/Python/filesystem probe result.
- Controlled executor privilege/bootstrap boundary được vận hành độc lập và audit được.
