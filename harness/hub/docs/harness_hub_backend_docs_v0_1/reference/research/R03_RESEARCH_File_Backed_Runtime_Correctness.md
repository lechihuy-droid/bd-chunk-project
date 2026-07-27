# R03 — File-backed Runtime Correctness trên Windows/Python

| Thuộc tính | Giá trị |
|---|---|
| Source ID | `HH-RES-R03` |
| Version | 0.2 |
| Ngày kiểm tra | 2026-07-27 |
| Trạng thái | Research — review required |
| Phạm vi áp dụng | Harness Hub local-v1, Python, một server process, local NTFS |
| Tài liệu đích | D03, D05, D07, D08 |

> Tài liệu này là nguồn nghiên cứu, không phải coding contract. Các đề xuất chỉ trở
> thành normative sau khi được duyệt và merge vào bộ design.

**Review note 0.2:** Revision này chốt projection + transaction journal là
recovery authority của local-v1; event chỉ là derived timeline. Journal chuyển
sang phase record immutable/checksummed; checkpoint recovery chuyển về per-run;
các guarantee NTFS/power-loss được hạ thành experiment-required.

## 1. Executive verdict

**NO-GO cho claim durability hiện tại; GO có điều kiện cho local-v1 single-process.**

- **[VERIFIED — CODE]** `run.json` và `state.json` được ghi qua file `.tmp` rồi
  `Path.replace`, nên có cơ chế tránh truncate trực tiếp file đích
  (`hub/services/runtime_state.py:107-111`).
- **[VERIFIED — CODE]** Không có `flush`, `os.fsync`, per-run lock, transaction
  journal, state version hay idempotency ledger trong các đường ghi được khảo sát.
- **[VERIFIED — CODE]** Event và child claim append trực tiếp vào JSONL; reader
  silently bỏ qua record JSON lỗi (`hub/services/runtime_events.py:23-25,36-46`;
  `hub/services/workflow_exec.py:127-131`).
- **[VERIFIED — CODE]** Checkpoint, `latest.json`, artifact và child output ghi đè
  trực tiếp bằng `write_text`, không temp-replace
  (`hub/services/runtime_checkpoint.py:39-43`;
  `hub/services/runtime_artifacts.py:30-35`;
  `hub/services/workflow_exec.py:123-126`).
- **[INFERRED]** Process crash, OS crash hoặc concurrent mutation có thể tạo ra:
  state mới nhưng thiếu event; event/artifact có nhưng state cũ; checkpoint hoặc
  `latest.json` bị cắt; mất update; JSONL có tail record bị cắt; artifact được công
  bố nhưng nội dung chưa durable.
- **[PROPOSED]** Giữ file-backed store cho local-v1, nhưng bắt buộc thêm:
  keyed per-run lock, durable atomic-file primitive, append primitive có tail
  repair, per-command transaction journal, monotonic state/event version,
  idempotency ledger, immutable artifact content + manifest-last publish, và
  startup recovery scan.
- **[UNKNOWN]** Không có bằng chứng trong repo hoặc experiment hiện tại đủ để
  đảm bảo directory-entry durability sau rename trên mọi phiên bản Windows,
  filesystem, storage controller và power-loss model. Claim chỉ được giới hạn
  đến cấu hình đã test: local NTFS, single host, single process.

Mục tiêu thực tế nên là:

1. không expose file JSON bị ghi nửa chừng sau process crash;
2. mọi giao dịch có chuỗi phase record hợp lệ đến `PREPARED` sẽ được
   roll-forward idempotent từ prior/target version đã xác minh;
3. event tail bị cắt được phát hiện và sửa có kiểm soát;
4. side effect bên ngoài không được gọi lại tự động nếu trạng thái hoàn tất chưa
   thể chứng minh;
5. recovery không silently skip corruption.

Không nên claim “exactly once”. Với CLI/API side effect không hỗ trợ idempotency,
crash sau khi bên ngoài đã thực thi nhưng trước khi Hub persist result tạo
**ambiguous outcome** không thể giải quyết chỉ bằng local files.

## 2. Scope và non-scope

### 2.1 Trong scope

- Atomic visibility và durability của JSON state/checkpoint trên Windows.
- JSONL append, torn tail, ordering và concurrent writer.
- Per-run locking trong một process và điều kiện cấm multi-process.
- Quan hệ state → event → checkpoint.
- Idempotency ledger và external-side-effect ambiguity.
- Artifact content/manifest ordering, orphan và quarantine.
- Crash injection, corruption recovery và migration path.

### 2.2 Ngoài scope

- Distributed consensus, multiple API replicas, network filesystem, SMB share.
- PostgreSQL/broker/outbox implementation.
- CLI sandbox và process isolation; xem R04.
- Provider capability cụ thể; xem R05.
- Chống storage-device firmware nói dối về flush/power-loss protection.

## 3. Evidence model

| Label | Ý nghĩa |
|---|---|
| `VERIFIED — CODE` | Quan sát trực tiếp từ code/test tại path:line |
| `VERIFIED — PRIMARY` | Được tài liệu Python/Microsoft/IETF chính thức hỗ trợ |
| `VERIFIED — EXPERIMENT` | Đã chạy experiment có môi trường/version ghi rõ |
| `INFERRED` | Suy luận trực tiếp từ evidence, chưa được experiment chứng minh |
| `PROPOSED` | Thiết kế khuyến nghị, chưa implement |
| `UNKNOWN` | Chưa đủ bằng chứng hoặc phụ thuộc platform/device |

Không có claim `VERIFIED — EXPERIMENT` trong revision 0.2; experiment được mô tả
ở §13 nhưng chưa chạy.

## 4. Baseline code audit

### 4.1 State và thread index

| Evidence | Phát hiện | Tác động |
|---|---|---|
| `hub/services/runtime_state.py:107-111` | temp name cố định `<file>.tmp`, `write_text`, rồi `replace` | Hai writer có thể tranh cùng temp; không flush; replace chỉ bao một file |
| `hub/services/runtime_state.py:213-231` | ghi `run.json` trước, sau đó ghi thread `state.json` | Crash giữa hai write làm thread index stale |
| `hub/services/runtime_state.py:235-238` | update là read → merge → write, không lock/version | Lost update khi hai command đồng thời |
| `hub/services/runtime_state.py:142-153,248-263` | list silently skip JSON/OSError | Corrupt active record có thể biến mất khỏi list mà không alert |
| `hub/services/runtime_reducers.py:81-92` | usage numeric được cộng khi merge | Retry cùng update có thể double-count; operation không idempotent |

**[INFERRED]** Temp file cố định không phải transaction isolation. Ngay cả khi
replacement của một pathname có atomic visibility, chuỗi `run.json` +
`thread/state.json` không atomic như một unit.

### 4.2 Event log

| Evidence | Phát hiện | Tác động |
|---|---|---|
| `hub/services/runtime_events.py:10-25` | event ID có timestamp giây + random suffix; không sequence/state version | Không phát hiện gap/out-of-order bằng contract |
| `hub/services/runtime_events.py:23-25` | text append, không lock/flush/fsync | Concurrent interleave hoặc mất tail sau crash |
| `hub/services/runtime_events.py:36-46` | malformed line bị `continue` | Corruption giữa log bị che giấu |
| `hub/services/runtime_events.py:57-59` | SSE replay toàn bộ parsed events | Record corrupt bị mất khỏi replay không có cảnh báo |

**[VERIFIED — PRIMARY]** Microsoft minh họa append có integrity bằng cách lock
vùng sắp ghi trước `WriteFile`, thay vì giả định append tự đủ an toàn
([Appending One File to Another File](https://learn.microsoft.com/en-us/windows/win32/fileio/appending-one-file-to-another-file)).

**[VERIFIED — PRIMARY]** Microsoft nêu single-sector write atomic nhưng
multi-sector write không được đảm bảo atomic nếu không dùng transaction; cached
multi-sector write cũng có thể chưa xuống disk
([WriteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile)).
Một JSON event không có giới hạn sector trong contract, vì vậy không được coi
mỗi line là atomic trên Windows.

### 4.3 Checkpoint và interrupt

| Evidence | Phát hiện | Tác động |
|---|---|---|
| `hub/services/runtime_checkpoint.py:39-43` | immutable checkpoint → `latest.json` → run state, cả ba write rời nhau | Mọi crash point tạo tổ hợp khác nhau |
| `hub/services/runtime_checkpoint.py:70-82` | list bỏ qua checkpoint corrupt | Có thể fallback nhưng không ghi operational alert |
| `hub/services/runtime_interrupts.py:27-43` | state interrupted → event → checkpoint | State mới có thể thiếu event/checkpoint |
| `hub/services/runtime_interrupts.py:79-98` | state running → event → checkpoint | Resume có thể được apply nhưng client retry lại do thiếu receipt |
| `hub/services/runtime_interrupts.py:70-72` | pending check không được bảo vệ bởi lock/version | Hai resume đồng thời có race |

### 4.4 Workflow và artifact

| Evidence | Phát hiện | Tác động |
|---|---|---|
| `hub/services/workflow_exec.py:288-289` | artifact content rồi event; state/node progress ở `:315-330` | Crash sau event nhưng trước state có artifact “thành công” trong run chưa tiến |
| `hub/services/runtime_artifacts.py:30-35` | node artifact ghi đè trực tiếp | Reader có thể gặp partial/truncated replacement |
| `hub/services/workflow_exec.py:123-131` | child output ghi trực tiếp; claim append trực tiếp | Child state/claim/artifact không có transaction boundary |
| `hub/services/workflow_exec.py:318-330` | state progress → checkpoint → event | Crash tạo missing event hoặc stale checkpoint pointer |
| `hub/services/workflow_exec.py:68-74` | fail state → checkpoint → error event | Client có thể không thấy terminal error event đã persisted |

### 4.5 Test coverage hiện tại

- **[VERIFIED — CODE]** Happy-path test xác nhận append/read event và
  checkpoint/latest (`hub/tests/test_runtime.py:83-104`).
- **[VERIFIED — CODE]** Artifact test xác nhận nội dung, list và existence của
  `artifact_written` event (`hub/tests/test_runtime_artifacts.py:54-65`).
- **[VERIFIED — CODE]** Workflow test xác nhận node checkpoint tồn tại
  (`hub/tests/test_workflow_exec.py:47-67`).
- **[VERIFIED — CODE]** Không tìm thấy crash injection, torn JSONL, concurrent
  update, stale version, idempotency replay, disk-full, replace-sharing violation,
  startup repair hoặc orphan scan trong các test được giao rà soát.

## 5. Platform facts: Windows khác POSIX ở đâu

### 5.1 Atomic replacement không đồng nghĩa durable commit

- **[VERIFIED — PRIMARY]** Python mô tả `os.replace(src, dst)` sẽ thay file đích
  và, nếu thành công, rename là atomic; cùng trang ghi rõ đây là yêu cầu POSIX.
  `Path.replace` là API mức cao để replace target
  ([Python `os.replace`](https://docs.python.org/3/library/os.html#os.replace),
  [Python `Path.replace`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.replace)).
- **[VERIFIED — PRIMARY]** Trên Windows, `MoveFileExW` có
  `MOVEFILE_REPLACE_EXISTING`; `MOVEFILE_WRITE_THROUGH` chỉ mô tả flush cho move
  thực hiện như copy + delete
  ([MoveFileExW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)).
- **[VERIFIED — PRIMARY]** `ReplaceFileW` có constant
  `REPLACEFILE_WRITE_THROUGH` nhưng Microsoft ghi là **not supported**
  ([ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)).
- **[INFERRED]** Vì code gọi `Path.replace` nhưng không flush temp trước, không
  được suy từ “rename atomic” thành “new bytes survive power loss”.
- **[UNKNOWN]** Mức guarantee chính xác của `Path.replace` đối với reader mở sẵn,
  antivirus/indexer sharing mode, rename metadata và sudden power loss trên cấu
  hình deployment chưa được empirical probe. Windows share-delete semantics có
  thể làm replace fail; caller phải xử lý failure, không silent retry vô hạn.

### 5.2 Flush Python buffer và OS buffer

- **[VERIFIED — PRIMARY]** Python yêu cầu `file.flush()` trước
  `os.fsync(file.fileno())`; trên Windows `os.fsync` gọi CRT `_commit`
  ([Python `os.fsync`](https://docs.python.org/3/library/os.html#os.fsync)).
- **[VERIFIED — PRIMARY]** Microsoft mô tả `_commit` ép OS ghi file tương ứng
  xuống disk
  ([MSVC `_commit`](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/commit)).
- **[VERIFIED — PRIMARY]** Windows thường buffer file writes;
  `FlushFileBuffers` chuyển buffered information của file tới device
  ([FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers),
  [Flushing system-buffered I/O](https://learn.microsoft.com/en-us/windows/win32/fileio/flushing-system-buffered-i-o-data-to-disk)).
- **[PROPOSED]** Mức local-v1: write bytes → `flush()` → `os.fsync()` → close →
  replace. Không cần unbuffered I/O cho mọi event vì alignment/complexity cao;
  batch flush theo transaction boundary.
- **[UNKNOWN]** Flush thành công vẫn phụ thuộc filesystem/device honoring flush.
  Không claim chống mọi controller/firmware/power-loss failure.

### 5.3 Locking

- **[VERIFIED — PRIMARY]** `LockFileEx` hỗ trợ shared/exclusive byte-range lock;
  exclusive lock chặn process khác read/write vùng đó; OS unlock khi process chết,
  nhưng Microsoft vẫn khuyên explicit unlock
  ([LockFileEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex)).
- **[PROPOSED]** Local-v1 dùng keyed `threading.RLock`/async-aware lock cho toàn
  command trên một run. Đây là đủ **chỉ khi đúng một process**.
- **[PROPOSED]** Startup phải reject `workers > 1`. File lock cross-process chỉ
  được thêm sau ADR riêng; không coi in-process lock là distributed lock.
- **[UNKNOWN]** Thư viện cross-platform lock nào sẽ được chọn nếu Gate E mở.
  Cần đánh giá semantics trên NTFS/SMB và stale-lock cleanup trước khi dùng.

### 5.4 Những POSIX assumption bị cấm

Không đưa các assumption sau vào Windows contract nếu chưa test:

- `fsync(directory_fd)` hoạt động giống Unix và đủ để persist rename;
- rename luôn thành công khi destination đang mở;
- một `write()` JSON line bất kỳ là atomic;
- append từ nhiều handle tự serialize record boundary;
- process close đồng nghĩa dữ liệu đã durable;
- lock file bằng “file tồn tại” tự giải phóng chính xác sau crash.

## 6. Consistency model đề xuất

### 6.1 Single writer và authoritative data

**[PROPOSED]**

- Runtime command handler là writer duy nhất của run mutation.
- Per-run command được serialize dưới một keyed lock.
- `run.json` là latest materialized projection; transaction journal immutable là
  recovery authority cho command đang commit hoặc commit chưa hoàn chỉnh.
- `events.jsonl` là **derived UI/audit/replay timeline**, không phải reducer
  authority của local-v1. Missing event được tái tạo từ committed/prepared
  transaction record bằng deterministic event ID; event không được dùng một mình
  để suy ra business state.
- Recovery projection lấy `run.json` hợp lệ + transaction chain hợp lệ. Nếu cả
  hai bất đồng và journal không chứng minh được prior/target transition, run
  chuyển `recovery_required`, không replay event để đoán state.
- Recovery-authoritative checkpoint chỉ thuộc **một run** và snapshot projection
  của run đó. Thread checkpoint/index chỉ là derived view, có thể rebuild.
- Artifact chỉ visible khi immutable manifest đã publish.

Điểm này chủ động resolve conflict với cách event-sourcing thuần: local-v1
không dùng event reducer làm source of truth. Nếu tương lai muốn event-sourced
authority, cần storage/migration ADR riêng và event schema đủ deterministic.

### 6.2 Version và identity

Mỗi run thêm:

```json
{
  "schema_version": 1,
  "state_version": 42,
  "last_event_sequence": 98,
  "last_transaction_id": "tx-..."
}
```

Mỗi event thêm:

```json
{
  "schema_version": 1,
  "event_id": "evt-...",
  "transaction_id": "tx-...",
  "state_version": 42,
  "sequence": 98,
  "type": "node.completed"
}
```

Invariant:

1. `state_version` tăng đúng một cho mỗi committed command mutation.
2. `sequence` tăng đúng một trong một run.
3. Event ID và transaction ID deterministic/persisted trước append lại.
4. Reader reject middle gap, duplicate ID có payload khác và state regression.
5. Duplicate ID cùng canonical hash được deduplicate trong recovery.

## 7. Primitive ghi file bắt buộc

### 7.1 `atomic_write_json_durable(path, object)`

**[PROPOSED]**

1. Serialize canonical UTF-8 bytes hoàn chỉnh trong memory.
2. Tạo temp unique trong **cùng directory**, ví dụ
   `.<name>.<txid>.<uuid>.tmp`, dùng create-exclusive.
3. Ghi toàn bộ bytes; kiểm tra short write/error.
4. `flush()` Python buffer.
5. `os.fsync(fd)`; nếu lỗi thì abort, không replace.
6. Close handle.
7. `os.replace(temp, path)`.
8. Read-back parse + verify `transaction_id/state_version/hash` cho critical file.
9. Temp còn lại do crash được startup scanner phân loại và quarantine/cleanup.

Guarantee được phép viết:

- **[UNKNOWN — EXPERIMENT REQUIRED]** Reader qua pathname trên target
  Windows/NTFS có luôn thấy old hoặc new complete JSON khi replace thành công hay
  không phải được chứng minh bằng R03-P01/P02. Python mô tả atomic rename nhưng
  Windows sharing mode và implementation path không đủ để report này nâng thành
  deployment guarantee.
- Không được viết: “mọi completed write chắc chắn sống qua sudden power loss”
  trước khi §13 experiment pass và directory metadata guarantee được chốt.

### 7.2 `append_event_durable(path, event)`

**[PROPOSED]**

1. Caller giữ per-run lock.
2. Canonical serialize thành một UTF-8 byte record kết thúc bằng `\n`.
3. Mở binary append một lần; ghi full record.
4. `flush()` và `os.fsync()` tại transaction commit boundary.
5. Cập nhật journal phase sau flush.

Không dựa vào single append là atomic. Recovery scan:

- EOF không có newline: truncate về byte offset ngay sau newline hợp lệ cuối,
  giữ phần cắt trong quarantine evidence.
- Line cuối có newline nhưng JSON/hash invalid: quarantine + truncate tail.
- Invalid UTF-8/JSON, sequence gap hoặc hash mismatch **ở giữa file**:
  `recovery_required`, không tự skip.
- Duplicate event ID cùng hash: bỏ duplicate khi project; khác hash: corruption.

Tail repair cũng là một transaction phục hồi:

1. Giữ per-run recovery lock và chặn reader/replay của run.
2. Scan byte offsets; lưu torn suffix, original length và SHA-256 vào một
   immutable/checksummed repair record.
3. Flush repair record trước khi truncate.
4. Truncate về last-valid-newline, `flush + fsync`.
5. Append lại event deterministic từ transaction record, `flush + fsync`.
6. Ghi immutable repair-complete record, rồi mới mở reader.

Crash sau bước 2 nhưng trước truncate: file gốc giữ nguyên, recovery lặp scan.
Crash sau truncate nhưng trước reappend: repair record chỉ ra suffix/event cần
tạo lại. Crash sau reappend nhưng trước complete: event ID/hash dedup làm bước
recovery idempotent. Nếu không có transaction record chứng minh event đúng,
không reappend bằng suy đoán.

### 7.3 Per-run checkpoint

**[PROPOSED]**

- Checkpoint nằm dưới `runs/<run-id>/checkpoints/`, filename immutable và ghi
  bằng atomic durable primitive.
- Checkpoint chứa `state_version`, `last_event_sequence`,
  `last_transaction_id`, workflow/profile hash và state hash.
- `latest-checkpoint.json` của run chỉ là atomic pointer/reference nhỏ.
- Nếu pointer lỗi/stale, scan per-run checkpoint hợp lệ và chọn checkpoint có
  version nằm trên validated transaction chain; không chọn chỉ theo timestamp.
- Thread-level checkpoint/index hiện tại là derived compatibility view. Nó không
  được dùng để phục hồi business state của run.

## 8. Exact command transaction protocol

File layout đề xuất:

```text
runs/<run-id>/
  run.json
  events.jsonl
  transactions/
    <tx-id>/
      00-intent.json
      10-dispatching.json
      20-prepared.json
      30-committed.json
  idempotency/
    <command-type>/<key-hash>.json
  artifacts/
```

### 8.1 Journal failure model

**[PROPOSED]** Không mutate một file journal qua các phase. Mỗi phase là record
immutable, create-exclusive, durable-write và checksum độc lập. Record sau chứa:

```json
{
  "schema_version": 1,
  "transaction_id": "tx-...",
  "phase": "PREPARED",
  "prior_state_version": 41,
  "target_state_version": 42,
  "prior_transaction_id": "tx-prev",
  "previous_phase_hash": "...",
  "payload_hash": "...",
  "record_hash": "..."
}
```

Validation:

- phase chỉ đi `INTENT → DISPATCHING? → PREPARED → COMMITTED`;
- mọi record verify canonical `record_hash` và `previous_phase_hash`;
- `prior_state_version` phải bằng current validated projection;
- `target_state_version = prior_state_version + 1`;
- `prior_transaction_id` phải nối đúng committed head của run;
- hai transaction cùng prior/target version là **fork**, không chọn theo time;
- missing phase/hash link là **gap**, không roll-forward qua gap;
- record file torn/invalid được quarantine; prior valid phase vẫn giữ nguyên;
- recovery theo validated version/hash chain, **không bao giờ theo creation time,
  mtime hay lexicographic transaction ID**.

Double-slot mutable journal (`slot-A`/`slot-B` với generation + checksum) chỉ là
alternative nếu benchmark chứng minh immutable phase records quá đắt. Nếu chọn,
reader lấy slot có generation cao nhất mà checksum và parent generation hợp lệ;
không overwrite cả hai slot trong cùng commit.

### 8.2 Pure state mutation

**[PROPOSED]**

1. Acquire per-run lock.
2. Load/validate run; verify expected `state_version`.
3. Lookup idempotency record:
   - `COMMITTED`: return stored response;
   - same key, different request hash: `409 IDEMPOTENCY_CONFLICT`;
   - `AMBIGUOUS`: fail closed/manual recovery.
4. Allocate `tx_id`, target `state_version`, event sequence(s), event IDs.
5. Create-exclusive immutable `INTENT` với command/request hash,
   prior/target version, prior transaction ID và record hash.
6. Compute new state/events/result without side effect.
7. Create-exclusive immutable `PREPARED` chứa previous-phase hash, canonical
   payload hashes và payload/reference đủ để roll-forward.
8. Atomic durable-write `run.json`.
9. Append + flush events.
10. Atomic durable-write checkpoint và latest pointer nếu command yêu cầu.
11. Atomic durable-write idempotency response `COMMITTED`.
12. Create-exclusive immutable `COMMITTED` nối hash tới `PREPARED`.
13. Release lock và response.

`PREPARED` phải chứa đủ redacted data/reference để lặp bước 8–12. Mọi bước
roll-forward phải idempotent theo `tx_id`, prior/target `state_version`,
`event_id` và content hash.

### 8.3 Command có external side effect

**[PROPOSED]**

1. Thực hiện bước 1–5 như trên.
2. Create-exclusive immutable `DISPATCHING`, lưu execution ID, prior phase hash
   và upstream idempotency-key reference/hash nếu provider hỗ trợ.
3. Gọi provider/CLI.
4. Persist raw normalized result/artifact content immutable.
5. Create-exclusive `PREPARED` với result reference/hash/classification; sau đó
   commit như bước 8–12.

Recovery:

- `INTENT` nhưng chưa `DISPATCHING`: safe abort/retry command.
- `DISPATCHING` không result:
  - upstream có idempotency/status lookup: reconcile bằng cùng key;
  - CLI/non-idempotent/không query được: `AMBIGUOUS`, không auto-run lại.
- Result durable + `PREPARED`: roll-forward, không gọi provider lại.

**[INFERRED]** Transaction journal đóng consistency gap giữa nhiều local files,
nhưng không tạo distributed transaction với provider/CLI.

## 9. Crash-point matrix

| # | Crash point | Trạng thái quan sát | Recovery bắt buộc | Auto-retry external? |
|---:|---|---|---|---|
| C01 | Trước durable `INTENT` | Không transaction | Command client có thể retry cùng key | Có, vì chưa dispatch |
| C02 | Sau `INTENT`, trước `DISPATCHING` | Intent chưa side effect | Abort hoặc resume deterministic | Có |
| C03 | Sau ghi `DISPATCHING`, trước call | Không biết call đã bắt đầu hay chưa | Reconcile theo provider key; nếu không có thì ambiguous | Chỉ khi upstream idempotent |
| C04 | Provider hoàn tất, trước result persist | External outcome có thể thành công nhưng local không biết | Query upstream; nếu CLI thì manual decision | Không mặc định |
| C05 | Result/content durable, trước `PREPARED` | Orphan result/content | Hash/tx metadata scan; attach nếu chứng minh được, nếu không quarantine | Không |
| C06 | `PREPARED`, trước `run.json` replace | Journal có full commit payload, state cũ | Roll-forward state | Không |
| C07 | Sau state replace, trước event append | State mới, missing event | Append deterministic events từ journal | Không |
| C08 | Giữa event record write | Torn JSONL tail | Truncate tail, append lại cùng event ID | Không |
| C09 | Sau event flush, trước checkpoint | State/event consistent, checkpoint stale | Tạo checkpoint từ prepared payload/state | Không |
| C10 | Sau checkpoint, trước idempotency commit | Projection đủ, client có thể retry | Mark ledger committed từ tx; return stored result | Không |
| C11 | Sau ledger commit, trước tx `COMMITTED` | Ledger/state/event đủ | Mark transaction committed | Không |
| C12 | Temp JSON complete, trước replace | Old target + orphan temp | Dựa journal quyết định replace hoặc quarantine | Không |
| C13 | Replace fail do sharing violation | Old target vẫn authoritative; temp tồn tại | Bounded retry dưới lock, rồi fail operational | Không |
| C14 | Disk full trong temp/event append | Temp/tail có thể partial | Fail closed; repair tail; alert disk-low | Không |
| C15 | Crash giữa artifact content và manifest | Content orphan, chưa visible | Verify/hash rồi attach từ prepared tx hoặc quarantine | Không |
| C16 | Manifest published, trước state reference | Manifest valid nhưng state cũ | Roll-forward state từ prepared tx | Không |
| C17 | State reference trước manifest — forbidden order | Dangling artifact | Recovery_required; đây là protocol bug | Không |
| C18 | Thread index update thiếu sau run commit | Run valid, thread stale | Rebuild derived thread index từ runs | Không |
| C19 | Phase record bị torn/invalid | Prior immutable phase còn valid | Quarantine record; dừng tại prior phase, validate chain | Theo prior phase |
| C20 | Hai tx cùng prior/target version | Journal fork | `recovery_required`; không chọn theo timestamp | Không |
| C21 | Crash sau repair record, trước truncate | Original torn tail còn nguyên | Lặp scan/verify repair intent | Không |
| C22 | Crash sau truncate, trước event reappend | Tail sạch nhưng event thiếu | Reappend deterministic từ tx + repair record | Không |
| C23 | Crash sau reappend, trước repair-complete | Event có thể đã tồn tại | Dedup bằng event ID/hash rồi complete repair | Không |

## 10. Artifact publish protocol

### 10.1 Layout

```text
artifacts/<artifact-id>/<version>/
  content
  manifest.json
```

### 10.2 Ordering

**[PROPOSED]**

1. Allocate immutable artifact/version IDs trong transaction.
2. Write content temp trong target directory; flush + fsync.
3. Rename thành immutable `content`; hash read-back.
4. Atomic durable-write `manifest.json` **sau content**, chứa:
   `artifact_id`, version, media type, byte length, SHA-256, creator tx/run/node.
5. Chỉ sau manifest hợp lệ mới đưa artifact reference vào `run.json`.
6. Sau state commit mới append `artifact.version_created`.

Visibility rule:

- list/read chỉ scan manifest hợp lệ;
- content không manifest là orphan, không expose;
- manifest thiếu content/hash mismatch là corruption, không trả partial bytes.

**[UNKNOWN — EXPERIMENT REQUIRED]** Trên Windows/NTFS, việc content đã được
flush/rename rồi manifest đã được flush/rename không tự chứng minh cả hai survive
cùng một power loss. R03-P04/P09 phải đo các tổ hợp: cả hai tồn tại, chỉ content,
manifest không content, và metadata stale. Manifest tồn tại nhưng content mất là
`STORAGE_CORRUPTION`: quarantine manifest, mark owning run `recovery_required`,
phát operational alert và không tự tạo content rỗng/không fallback sang path khác.

### 10.3 Orphan policy

| Tuổi/origin | Hành động |
|---|---|
| Thuộc active `INTENT/PREPARED` | Giữ; recovery quyết định |
| Không transaction, nhỏ hơn grace window | Giữ tạm để tránh race |
| Không transaction, quá grace window | Move vào `quarantine/orphans/<scan-id>` |
| Manifest/hash mismatch | Quarantine ngay + operational alert |

Không delete evidence tự động trước backup/retention window.

## 11. Idempotency ledger

Ledger key scope: `(run_id, command_type, idempotency_key)`.

Record tối thiểu:

```json
{
  "schema_version": 1,
  "run_id": "run-...",
  "command_type": "interrupt.resolve",
  "idempotency_key_hash": "...",
  "request_hash": "...",
  "transaction_id": "tx-...",
  "status": "INTENT|DISPATCHING|COMMITTED|AMBIGUOUS|FAILED",
  "response_hash": "...",
  "response_ref": "results/<tx-id>.json",
  "response_classification": "internal",
  "created_at": "...",
  "updated_at": "..."
}
```

Rules:

- Không lưu raw secret trong ledger; key được hash/HMAC theo ADR security.
- Ledger không chứa raw response, prompt, provider output hoặc secret. Nó chỉ lưu
  redacted response reference, canonical hash và data classification. Referenced
  response áp dụng retention/encryption/access policy riêng.
- Same key + same canonical request hash + `COMMITTED` resolve `response_ref`,
  verify hash/classification rồi trả response đã được policy cho phép.
- Same key + different hash trả conflict.
- Ledger commit phải sau state/event commit nhưng trước response.
- Ledger `AMBIGUOUS` không được tự đổi thành `FAILED` và retry side effect.
- Retention phải dài ít nhất bằng API retry window + backup/recovery window.

**[PROPOSED]** Usage counters không được cộng lại khi replay. Persist absolute
per-execution usage keyed theo execution ID rồi derive aggregate, thay vì áp lại
numeric merge ở `hub/services/runtime_reducers.py:81-92`.

## 12. Recovery algorithm

Startup scan phải chạy trước khi nhận mutation mới:

1. Acquire global startup barrier; không nhận command write.
2. Enumerate run directories bằng validated IDs.
3. Parse `run.json`; nếu invalid, tìm per-run transaction/checkpoint hợp lệ.
4. Scan JSONL bytes:
   - repair torn tail theo ordered repair transaction ở §7.2;
   - fail closed với middle corruption/gap/hash conflict.
5. Validate state version, last sequence và last transaction.
6. Verify checksum/phase link của từng transaction; dựng chain theo
   `prior_transaction_id` và prior/target state version:
   - fork, version gap hoặc phase-hash gap: `recovery_required`;
   - `INTENT`: abort nếu chắc chắn chưa dispatch;
   - `DISPATCHING`: reconcile hoặc mark `AMBIGUOUS`;
   - `PREPARED`: roll-forward idempotently;
   - local commit đủ nhưng thiếu `COMMITTED`: tạo immutable committed record.
   Recovery không dùng creation order, mtime hoặc timestamp để chọn transaction.
7. Rebuild stale per-run `latest-checkpoint.json` từ checkpoint nằm trên
   validated transaction chain.
8. Scan artifact manifest/content/hash; quarantine orphan/corruption.
9. Rebuild thread `runs/latest_run_id` như derived index.
10. Write recovery audit event/report; không append vào corrupt log đang fail closed.
11. Run ở trạng thái `recovery_required` nếu còn sequence gap, ambiguous external
    outcome, dangling manifest hoặc không tìm được valid projection.
12. Chỉ mở mutation API sau recovery scan; read API phải hiển thị degraded state.

### 12.1 Source of truth khi bất đồng

| Trường hợp | Quyết định |
|---|---|
| `PREPARED` chain valid, state cũ đúng prior version | Journal thắng để roll-forward |
| State mới, event thiếu, matching tx chain valid | Projection + journal tạo lại derived event |
| Event mới, state cũ, matching journal valid | Bỏ qua event như authority; journal roll-forward state |
| State/event khác nhau, không journal | Không tự đoán; `recovery_required` |
| Per-run pointer corrupt, checkpoint trên valid tx chain | Rebuild pointer |
| Thread index stale, run valid | Rebuild index từ run |
| Artifact content không manifest | Orphan, không expose |
| Manifest không content/hash mismatch | Quarantine; run `recovery_required` |

## 13. Experiments và test catalogue

### 13.1 Windows empirical probe

Môi trường phải ghi:

- Windows build, Python version/build;
- filesystem (`fsutil fsinfo volumeinfo`), local/VM;
- storage type/controller, antivirus/indexer state;
- process crash (`TerminateProcess`) và VM hard-reset/power-cut simulation tách riêng.

| Test ID | Experiment | Pass condition |
|---|---|---|
| R03-P01 | Loop reader + atomic replace writer, 100k iterations | Reader chỉ parse old/new complete JSON; replace errors được đếm |
| R03-P02 | Giữ destination open với các share modes rồi replace | Matrix thành công/failure có bounded handling |
| R03-P03 | Kill process tại từng primitive step | State là old/new complete; temp được scan |
| R03-P04 | Hard-reset VM sau flush/replace checkpoints | Kết quả được phân loại; không overclaim ngoài observed config |
| R03-P05 | Hai concurrent commands cùng run | Lock/version ngăn lost update |
| R03-P06 | Hai run khác nhau | Có concurrency, không global serialization quá mức |
| R03-P07 | Append event lớn hơn sector, kill giữa write | Torn tail phát hiện/truncate/reappend |
| R03-P08 | Inject malformed line giữa JSONL | Fail closed, không silently skip |
| R03-P09 | Disk-full/permission/sharing violation | Không publish partial state/artifact; operational error rõ |
| R03-P10 | Crash C01–C23 | Recovery outcome đúng matrix |

### 13.2 Normative test mapping

| Requirement | Existing/new ID | Bổ sung |
|---|---|---|
| State transition + version | `ST-001`, `ST-002` | concurrent stale-write/property tests |
| Ordered event/replay | `EV-001` | sequence/hash/duplicate deterministic |
| Corrupt/gap/late event | `EV-002` | torn tail repair; middle corruption fail closed |
| Immutable artifact/hash | `AR-001` | content-first/manifest-last, orphan scan |
| Restart during attempt | `OPS-001` | C01–C23 crash injection |
| Backup/restore | `OPS-002` | include journal/ledger/quarantine; rebuild index |
| API idempotency | `API-001` | same key replay, hash conflict, ambiguous response |

### 13.3 Test implementation constraints

- Fault injection đặt ngay sau từng durable boundary, không dùng timing sleep.
- Mỗi test assert cả filesystem layout, public state và operational signal.
- Golden recovery chạy ít nhất trên Windows CI/host thực.
- POSIX test không thay thế Windows probe.
- Real provider không cần cho deterministic suite; external outcomes dùng fake
  adapter có controllable idempotency/status lookup.

## 14. ADR recommendations

### ADR-R03-01 — Giữ file-backed store với hard single-process guard

**Decision đề xuất:** Accept cho local-v1; startup reject multi-worker mutation.

Alternatives:

- SQLite ngay: consistency tốt hơn, nhưng migration/scope lớn hơn hiện tại.
- Cross-process file lock: chưa đủ evidence và vẫn không giải quyết multi-file tx.

Exit condition: khi cần multi-process, shared host, remote filesystem hoặc hơn một
writer, mở Gate E và chuyển storage/transaction ADR; không chỉ thêm worker.

### ADR-R03-02 — Durable atomic-file primitive dùng chung

**Decision đề xuất:** Mọi state/checkpoint/manifest/ledger/journal write dùng một
primitive temp-unique + flush + fsync + replace + validation. Cấm `write_text`
trực tiếp cho mutable critical JSON.

### ADR-R03-03 — Per-command transaction journal

**Decision đề xuất:** Journal dùng immutable/checksummed phase records
`INTENT/DISPATCHING/PREPARED/COMMITTED`, nối prior/target state version và hash
chain để bridge projection/event/checkpoint/artifact/ledger. Cấm recovery theo
creation order; fork/gap chuyển `recovery_required`.

Rejected: “state write rồi best-effort event” vì crash tạo missing audit/replay.

### ADR-R03-04 — Event log corruption policy

**Decision đề xuất:** Chỉ tự repair torn tail; corruption/gap giữa log fail closed.
Không silently skip active runtime event.

### ADR-R03-05 — External side-effect semantics

**Decision đề xuất:** At-least-once command receipt + idempotent local commit;
external exactly-once không được claim. `DISPATCHING` không reconcile được chuyển
`AMBIGUOUS`, cần explicit/human retry.

### ADR-R03-06 — Artifact manifest-last publication

**Decision đề xuất:** Immutable content, verify hash, atomic manifest, state
reference, event. List/read chỉ expose manifest valid.

### ADR-R03-07 — Derived thread index

**Decision đề xuất:** `thread/state.json` là rebuildable index, không cùng
transaction authority với run. Recovery rebuild từ runs thay vì fail cả run.

## 15. Mapping vào normative design

| Finding/decision | Tài liệu | Section cần revise | Test IDs |
|---|---|---|---|
| Atomic visibility ≠ durability | D05 | Atomicity và locking | `OPS-001`, R03-P01–P04 |
| Per-run lock + single-process guard | D03, D05, D07 | Command model; deployment constraints | `ST-002`, R03-P05–P06 |
| Transaction journal | D03, D05 | State/event ordering; storage layout | `EV-001`, `OPS-001` |
| Event sequence/tail repair/fail closed | D03, D05 | Event contract; recovery | `EV-001`, `EV-002` |
| Idempotency + ambiguous external outcome | D03, D05 | Idempotency; error/retry | `ST-002`, `API-001`, `OPS-001` |
| Checkpoint immutable + pointer rebuild | D03, D05 | Checkpoint/replay | `EV-002`, `OPS-001` |
| Manifest-last artifact | D05 | Artifact/storage contract | `AR-001`, `OPS-001` |
| Recovery SLO phải đo sau scan prototype | D07 | SLO; startup/recovery | `OPS-001`, `OPS-002` |
| Crash/disk-full/Windows CI matrix | D08 | Phase 2; test matrix; Gate C | `EV-*`, `OPS-*`, R03-P* |

### 15.1 Cụm câu cần hạ mức guarantee trước khi implementation

- D07 “Runtime state loss = 0 completed atomic writes” chỉ hợp lệ trong
  durability envelope được định nghĩa ở Gate C, sau khi durable primitive và
  Windows experiment pass.
- D07 RPO phải là: không mất transaction đã có valid `COMMITTED` chain; valid
  `PREPARED` có thể roll-forward; `DISPATCHING` external side effect có thể
  `AMBIGUOUS`; sudden power loss ngoài documented Windows/NTFS envelope không
  được bảo đảm.
- D05 “flush trước response” phải chỉ rõ `file.flush + os.fsync`, file nào và
  transaction boundary nào.

## 16. Go/no-go gates

### Gate Phase 2 / Runtime hardening

GO khi:

- ADR-R03-01..07 được owner duyệt;
- durable primitives và per-run lock có test;
- crash matrix C01–C23 được implement bằng deterministic fault injection;
- active corruption không còn silently skip;
- transaction recovery và idempotency replay pass trên Windows.

### Gate C / Local v1

GO khi:

- R03-P01–P10 pass trên documented Windows/NTFS target;
- backup/restore bao gồm journal, ledger, artifacts và quarantine;
- startup reject multi-worker;
- ambiguous external side effect có operator-visible workflow;
- SLO recovery được benchmark với 1,000 local runs.

Gate C chỉ pass khi release note và D07 ghi cùng **accepted durability envelope**:

| Dimension | Accepted envelope |
|---|---|
| Host/storage | Một process, một host, local NTFS; không SMB/network/removable FS |
| Failure | Process kill/restart và tested Windows/VM hard-reset scenarios |
| Committed RPO | Không mất transaction có valid immutable `COMMITTED` chain trong experiment matrix |
| Prepared RPO | Valid `PREPARED` được deterministic roll-forward |
| Dispatching RPO | Có thể `AMBIGUOUS`; không claim exactly-once |
| Event | Derived timeline; missing event được regenerate từ tx, không làm mất projection |
| Artifact | Chỉ manifest+content hash-valid mới visible; mismatch fail closed |
| Exclusion | Không guarantee storage firmware/controller không honor flush hoặc configuration chưa test |

Nếu R03-P04 không chứng minh power-loss survival ổn định, Gate C vẫn chỉ có thể
pass với envelope hẹp hơn: process-crash durability, backup-based recovery cho
machine/power loss, và D07 phải hạ RPO tương ứng. Không được giữ câu “0 completed
atomic writes lost” trong trường hợp này.

NO-GO nếu:

- còn direct critical `write_text`/unflushed append;
- state/event/checkpoint có thể lệch mà không journal;
- retry tự động CLI/non-idempotent sau `DISPATCHING`;
- corruption giữa JSONL bị skip;
- artifact được expose trước manifest/hash validation.

## 17. Open questions

| ID | Câu hỏi | Owner/experiment | Trạng thái |
|---|---|---|---|
| OQ-01 | Directory-entry durability cần native Windows flush strategy nào? | Backend + R03-P04 | `UNKNOWN` |
| OQ-02 | Antivirus/indexer sharing violation rate và retry budget? | Ops + R03-P02 | `UNKNOWN` |
| OQ-03 | Max event size để cap torn-write blast radius? | Backend/Security | `PROPOSED` |
| OQ-04 | Quarantine retention/disk quota? | Ops/Security | `PROPOSED` |
| OQ-05 | Provider nào hỗ trợ idempotency/status reconciliation? | R05 | `UNKNOWN` |
| OQ-06 | Khi nào chuyển SQLite/PostgreSQL? | Architecture Gate E | `PROPOSED` |

## 18. Confidence

| Kết luận | Confidence |
|---|---:|
| Code hiện tại thiếu flush/lock/journal/idempotency | High |
| Có các crash gap đã liệt kê | High |
| Temp + replace giảm nguy cơ expose truncate trực tiếp | High |
| Windows/NTFS reader luôn thấy old/new complete file | Unknown, phải qua R03-P01/P02 |
| Protocol journal có thể phục hồi multi-file local commit | Medium-high, cần prototype |
| Power-loss durability trên mọi Windows/storage target | Low/unknown |
| Single-process file-backed đủ cho local-v1 sau hardening | Medium-high |

## 19. Primary-source bibliography

1. Python Software Foundation,
   [`os.replace`](https://docs.python.org/3/library/os.html#os.replace).
2. Python Software Foundation,
   [`os.fsync`](https://docs.python.org/3/library/os.html#os.fsync).
3. Python Software Foundation,
   [`pathlib.Path.replace`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.replace).
4. Microsoft,
   [`MoveFileExW`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw).
5. Microsoft,
   [`ReplaceFileW`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew).
6. Microsoft,
   [`FlushFileBuffers`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).
7. Microsoft,
   [Flushing System-Buffered I/O Data to Disk](https://learn.microsoft.com/en-us/windows/win32/fileio/flushing-system-buffered-i-o-data-to-disk).
8. Microsoft,
   [`_commit`](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/commit).
9. Microsoft,
   [`WriteFile`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-writefile).
10. Microsoft,
    [`LockFileEx`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex).
11. Microsoft,
    [Appending One File to Another File](https://learn.microsoft.com/en-us/windows/win32/fileio/appending-one-file-to-another-file).

## 20. Traceability

- Nguồn local được đọc: `runtime_state.py`, `runtime_events.py`,
  `runtime_checkpoint.py`, `runtime_reducers.py`, `runtime_interrupts.py`,
  `runtime_artifacts.py`, `workflow_exec.py` và các runtime/workflow tests được
  liệt kê tại §4.5.
- Không thay đổi source code hoặc normative design trong research revision này.
- Revalidate khi Python/Windows target thay đổi, storage chuyển khỏi local NTFS,
  multi-worker được bật, hoặc trước Gate C.

## 21. Change log

| Version | Date | Thay đổi |
|---|---|---|
| 0.1 | 2026-07-27 | Baseline code/platform research và protocol ban đầu |
| 0.2 | 2026-07-27 | Cross-review: projection+journal authority; immutable phase chain; per-run checkpoint; NTFS guarantees hạ thành unknown; ordered tail repair; redacted ledger; Gate C durability envelope |
