# D03 — Runtime State, Events and Recovery

```yaml
document_id: HH-DES-D03
version: 1.1
status: In Review
owner: Runtime
depends_on: [D01, D02]
research_sources: [HH-RES-R03, HH-RES-R07]
```

## 1. Runtime responsibilities

Runtime tạo run, snapshot definition/profile, schedule node tuyến tính, mở attempt, kiểm tra policy/interrupt, gọi Gateway, persist result/artifact, transition state, checkpoint và stream event. Chỉ Runtime được mutate run/node state.

## 2. State models

### Run

`queued | running | interrupted | cancelling | succeeded | failed | cancelled`

| Current | Trigger/guard | Action | Next | Event |
|---|---|---|---|---|
| — | create valid snapshot | persist run v1 | queued | `run.created` |
| queued | start; no pending interrupt | set started | running | `run.started` |
| running | approval/validation requires human | persist interrupt | interrupted | `interrupt.created` |
| interrupted | resolve=resume; expected version | mark interrupt resolved | running | `interrupt.resolved` |
| interrupted | resolve=reject | terminalize | failed | `run.failed` |
| running/interrupted | cancel command | mark cancelling | cancelling | `run.cancelling` |
| cancelling | no active attempt/process | finalize | cancelled | `run.cancelled` |
| running | all nodes succeeded | finalize | succeeded | `run.succeeded` |
| queued/running | unrecoverable error | persist error | failed | `run.failed` |

Terminal states: `succeeded`, `failed`, `cancelled`.

### Node attempt

`pending | ready | running | interrupted | succeeded | failed | cancelled | timed_out`

Mỗi retry tạo `attempt_no + 1`. `succeeded/failed/cancelled/timed_out` terminal. Node projection lấy attempt cuối nhưng giữ toàn bộ history.

### Interrupt

`pending | resolved | expired`. Pending chỉ chuyển một lần; conflicting duplicate trả `409 COMMAND_CONFLICT`.

## 3. Command envelope

```json
{
  "schema_version": 1,
  "command_id": "cmd-...",
  "type": "run.resume",
  "run_id": "run-...",
  "expected_version": 7,
  "idempotency_key": "...",
  "issued_at": "2026-07-27T00:00:00Z",
  "principal": {"kind":"local_user"},
  "payload": {}
}
```

Commands v1: `run.start`, `run.cancel`, `run.resume`, `interrupt.resolve`, `attempt.retry`. Mọi command mutation kiểm tra expected version và idempotency trước side effect.

## 4. Event envelope

```json
{
  "schema_version": 1,
  "event_id": "evt-...",
  "run_id": "run-...",
  "thread_id": "thread-...",
  "sequence": 12,
  "type": "attempt.completed",
  "occurred_at": "2026-07-27T00:00:01Z",
  "correlation_id": "corr-...",
  "causation_id": "cmd-...",
  "payload": {}
}
```

Rules:

- `sequence` tăng đơn điệu trong một run.
- `event_id` unique; replay dedup theo ID.
- Event là derived timeline cho UI/diagnostic, không phải recovery authority.
- Event chỉ được emit từ committed transaction; thiếu event được regenerate từ transaction journal.
- SSE `id` bằng sequence/event ID và `event` bằng event type.
- Event không chứa raw secret, full prompt/output nhạy cảm; dùng `*_ref`.

Catalogue tối thiểu:

`run.created/started/interrupted/cancelling/succeeded/failed/cancelled`,  
`node.ready`, `attempt.started/progress/completed/failed/cancelled/timed_out`,  
`interrupt.created/resolved/expired`, `artifact.version_created`,  
`route.selected`, `policy.denied`, `checkpoint.created`, `error`.

## 4.1 Recovery authority và transaction journal

Target local v1 không claim event sourcing. Recovery authority là:

```text
immutable checksummed transaction phase records
  + committed run projection
  + per-run recovery checkpoint
```

Mỗi command ghi immutable phase record có:

- `transaction_id`, `command_id`, `idempotency_key`;
- `prior_state_version`, `target_state_version`;
- `prior_transaction_hash`;
- canonical request hash;
- phase `prepared | side_effect_started | side_effect_observed | committed | aborted`;
- projection hash, response reference/hash/classification;
- checksum của record.

Recovery validate chain theo state version/hash. Fork, gap, corrupt record hoặc hai transaction cùng target version phải fail closed và chuyển run sang `recovery_required`. Không dùng timestamp, file creation time hoặc directory enumeration làm commit order.

## 5. Execution loop

```text
load run + validate version
while non-terminal:
  if cancellation: cancel active execution, persist, finish
  if pending interrupt: persist interrupted, return
  select next node from immutable IR
  evaluate stop budget + policy
  create attempt and checkpoint
  execute deterministic validator OR Gateway request
  validate result
  persist artifact/result
  commit transaction + projection
  derive events and per-run checkpoint
```

Runtime checks time/call/node budgets before launch và during stream. Budget exhausted là normalized failure/interrupt theo policy, không launch thêm provider call.

## 6. Idempotency và concurrency

- Key scope: `(run_id, command_type, idempotency_key)`.
- Store request hash + status + final response reference.
- Idempotency ledger không lưu raw response; chỉ lưu redacted `response_ref`, response hash, classification và retention.
- Same key/same hash trả response cũ; same key/different hash trả `409 IDEMPOTENCY_CONFLICT`.
- Expected version mismatch trả `409 STALE_RUN_VERSION`; không side effect.
- Per-run lock là đủ cho single process. Multi-process deployment bị cấm nếu chưa thay storage/locking ADR.

## 7. Checkpoint, event regeneration và replay

Checkpoint tạo sau:

- run start;
- node/attempt terminal;
- interrupt create/resolve;
- run terminal.

Recovery-authoritative checkpoint luôn nằm trong scope một run và chứa state projection, state version, committed transaction hash, `last_event_sequence`, workflow/profile hashes và reason. Thread checkpoint/index chỉ là derived projection.

Recovery:

1. load latest valid checkpoint;
2. verify transaction/projection/hash chain;
3. complete hoặc abort unfinished transaction theo recorded phase;
4. regenerate missing derived events từ committed transaction;
5. quarantine torn/corrupt event tail bằng journaled repair;
6. không replay provider side effect.

Event replay chỉ phục vụ UI/diagnostic. Event payload v1 không được dùng để mutate projection.

## 8. Restart recovery

Khi startup scan:

- `queued`: có thể start lại.
- `running` có attempt non-terminal: mark attempt `failed` với `PROCESS_LOST`; không giả định provider chưa chạy.
- Nếu provider có stable execution ID và reconciliation/idempotency đã được chứng minh, Runtime có thể reconcile. Nếu không, trạng thái side effect là ambiguous và phải tạo human/explicit retry; không tự retry side-effecting CLI.
- `interrupted`: giữ nguyên.
- `cancelling`: finalize khi không còn tracked process.
- terminal: không đổi.

Corrupt JSON/JSONL không được silently skip đối với runtime active. Tail repair phải ghi repair intent, copy+hash quarantine, durable truncate, regenerate deterministic records và ghi repair receipt; crash ở mỗi bước phải recoverable.

Power-loss durability của replace/rename trên Windows/NTFS là `UNKNOWN` cho đến khi R03 probe matrix pass trên supported OS/Python/filesystem. Gate C chỉ claim process-crash consistency trong envelope đã kiểm chứng; RPO không được mạnh hơn evidence.

## 9. Cancellation

Cancellation cooperative trước, hard kill sau grace period. Gateway chuyển cancel tới Executor. CLI phải kill process tree; API adapter cancel upstream nếu capability có. Late events sau terminal được ghi diagnostic và ignore cho state.

## 10. Failure classification

- `VALIDATION/POLICY/AUTH/CAPABILITY/CONTRACT`: không retry/fallback.
- `TRANSIENT_TRANSPORT/RATE_LIMIT`: adapter retry bounded trên cùng provider.
- `PROVIDER_UNAVAILABLE`: Gateway có thể đề xuất fallback; Runtime mở attempt mới.
- `TIMEOUT/CANCELLED/PROCESS_LOST`: Runtime quyết định explicit retry theo idempotency.
- `INTERNAL/STORAGE_CORRUPTION`: fail closed và require recovery.

## 11. Acceptance

- Property/table tests phủ mọi transition hợp lệ và không hợp lệ.
- Duplicate resume/cancel không chạy node hai lần.
- Stale command không mutate state.
- Transaction chain recovery và derived-event regeneration deterministic.
- Restart giữa attempt không tạo artifact/result trùng.
- Late/duplicate/out-of-order event không phá terminal state.
- Fork/gap/corrupt journal fail closed.
- R03 crash points C01–C23 và probes P01–P10 pass trong durability envelope được owner duyệt.
