# Design Doc — Nhóm B: Agent-Execution Runtime (SAFEHARNESS lõi)
**Date:** 2026-06-28 · **Author:** Claude (Opus 4.8) · **Status:** 🔵 Design (tiền-SDD)

> Tài liệu thiết kế cho **Nhóm B** trong `UPGRADE-safeharness-plan.md`: biến harness thành **runtime điều phối vòng lặp agent**, gate mọi tool-call qua L1–L4. Đây là chokepoint duy nhất giữa model và môi trường. Doc này là tham chiếu để mở SDD từng item; chưa phải RD.

---

## 0. Phạm vi & quan hệ với Nhóm A

Nhóm A (observe/governance thô trên log + suite) cung cấp **nguyên liệu** mà Nhóm B **tái dùng và nâng từ "quan sát" lên "thực thi (enforce)"**:

| Nhóm A (observe) | Nhóm B nâng lên (enforce) |
|---|---|
| A3 — 5 risk-tier *gắn nhãn* | L3 — *chặn* theo tier + capability token |
| A1 — Entropy *hiển thị* | Entropy Monitor *bypass fast-path* khi θ vượt |
| A2 — Provenance *hiển thị* | L1/L2 — *điều chỉnh mức thẩm định* theo provenance |
| A4 — HMAC ký *suite manifest* | L3 — HMAC ký *tool-description* trong registry |
| A5 — Violation *report* | L4 — Violation *kích hoạt rollback/degradation* |

→ Làm Nhóm A trước là đúng: B chỉ thêm "tay điều khiển" lên dữ liệu A đã có.

**Điều kiện tiên quyết của toàn Nhóm B:** harness phải **chạy agent loop** (mọi tool-call đi qua harness). Không có loop ⇒ không có chokepoint ⇒ L1–L4 vô nghĩa.

---

## 1. Kiến trúc — B0 Execution Loop (chokepoint)

```
        ┌───────────────────────── HARNESS RUNTIME (chokepoint) ─────────────────────────┐
 user → │ L1 INFORM (khử khuẩn input) → [decide] LLM → tool_call                           │
        │      ↑                                   │                                        │
        │   provenance                       L3 CONSTRAIN (token+tier+HMAC)  ──reject──▶ tool_result(is_error)
        │                                          │ allow                                  │
        │                                   L2 VERIFY (Rule→Judge→Causal) ──INJECTION──▶ L4 rollback
        │                                          │ pass                                   │
        │                                   EXECUTE tool (confined) → L1 re-sanitize output │
        │                                          │                                        │
        │                                   L4 CORRECT: checkpoint + update protected memory│
        └───────────────────────────────────────────────────────────────────────────────────┘
```

### B0 — hai phương án engine (quyết định kiến trúc bắt buộc)
| | (A) Bọc `codex exec` + git checkpoint | (B) `anthropic` manual tool-loop |
|---|---|---|
| Gate per-tool-call | ❌ chỉ gate ranh giới pha + diff | ✅ gate **từng** tool-call (approve/reject/edit args) |
| L1/L2/L3/L4 đầy đủ | một phần | ✅ đủ |
| API key / cost | **không** | **cần** ANTHROPIC_API_KEY + tốn token |
| Build | nhỏ (tái dùng Track B Phase 1) | lớn hơn (tự viết loop) |

**SAFEHARNESS đầy đủ (per-tool L1–L4) ⇒ cần phương án (B).** Mầm phương án (A) đã có ở Track B Phase 1 (worktree + approve + rollback). Khuyến nghị: B0 chốt **(B)** với model `claude-opus-4-8`, `thinking={"type":"adaptive"}`, `effort:"xhigh"`, streaming; key đặt ở `.env` (Claude không nhập). Tools (bash/edit/read) **confined trong git-worktree của job** (tái dùng isolation Phase 1).

---

## 2. Vòng lặp Plan-Execute-Verify (Algorithm 1) — thứ tự thực thi

> **L3 chạy TRƯỚC L2** để tiết kiệm: hành động đã bị cấm quyền thì không gọi Judge model đắt.

1. **Session Init** — cấp **Capability Tokens** (TTL + max-invocation) cho tập tool được phép.
2. **L1 Inform** — khử khuẩn input + history (NFKC, bỏ zero-width/bidi, regex, semantic filter).
3. **Decide** — LLM sinh phản hồi chứa tool_call.
4. **L3 Constrain** — kiểm token + risk-tier; sai ⇒ reject ngay (tool_result is_error).
5. **L2 Verify** — Rule → Contextual Judge → Causal Diagnostics; phát hiện injection ⇒ L4.
6. **Execute + re-sanitize** — chạy tool (confined), **lọc lại output (L1)** trước khi vào memory (chống Indirect Prompt Injection).
7. **Update + Checkpoint (L4)** — ghi protected memory + điểm khôi phục.

---

## 3. Chi tiết từng item

### B1 — L1 INFORM (toàn vẹn dữ liệu)
- **Khử khuẩn cấu trúc:** NFKC normalize; loại zero-width spaces, bidi-control, homoglyph; chuẩn hoá hướng văn bản.
- **Lọc ngữ nghĩa (khi nghi):** LLM phụ (rẻ, vd `claude-haiku-4-5`) trích "dữ liệu thực", loại imperative cố ghi đè hệ thống.
- **Áp cho:** input người dùng **và** tool-output (RAG/web/bash) **trước khi** vào memory.
- **Tái dùng A2:** content provenance=untrusted ⇒ bắt buộc qua L1 nặng.
- **Lives in:** `runtime/inform.py`. **Open Q:** ngưỡng "khi nghi" (regex pattern set) và có luôn bật semantic filter hay chỉ khi flag.

### B2 — L2 VERIFY (xác thực đa tầng)
- **Tier 1 Rule-based:** allowlist/denylist + pattern (rẻ, fast-path).
- **Tier 2 Contextual Judge:** LLM thẩm định *kết hợp lịch sử suy luận gần đây* → phân biệt "ý định hợp lệ" vs "injection ẩn".
- **Tier 3 Causal Diagnostics:** phân tích nguyên nhân — hành động do logic nghiệp vụ hay do payload độc kích hoạt.
- **Entropy bypass:** nếu violation-rate (A1, w=20) > θ=0.3 ⇒ **tắt fast-path Tier 1**, ép mọi action qua Tier 2/3.
- **Lives in:** `runtime/verify.py`. **Open Q:** model nào cho Judge; định nghĩa "INJECTION confirmed" → trigger L4.

### B3 — L3 CONSTRAIN (đặc quyền tối thiểu)
- **5 risk-tier enforce** (nâng A3): `read_only/write/execute/network/destructive` — chặn theo cấp degradation hiện tại.
- **HMAC-SHA256 tool-description** trong registry (nâng A4): ký mô tả tool; verify trước mỗi lần dùng ⇒ chống **T4 Tool-Description Injection** (vd tool tự BCC email).
- **Capability Tokens:** mỗi token có **TTL** + **Maximum Invocation Count**; hết hạn/hết lượt ⇒ thu hồi quyền ⇒ giới hạn blast-radius nếu agent bị chiếm.
- **Lives in:** `runtime/constrain.py`, `runtime/registry.py`. **Open Q:** schema token; nơi giữ HMAC key (`.env`, không commit); tool nào vào tier nào (mặc định từ A3 `risk_tiers.json`).

### B4 — L4 CORRECT (khôi phục & hạ cấp)
- **Checkpointing + Rollback:** khôi phục **cả file system (git worktree — đã có Phase 1) VÀ memory store** về checkpoint an toàn gần nhất khi xác nhận tấn công.
- **5 cấp Adaptive Degradation:** Level 0 (toàn quyền) → Level 4 (chỉ read_only). Mức tăng ⇒ vô hiệu hoá nhóm tool rủi ro (vd Level 2 tắt `network` + `destructive`).
- **Lives in:** `runtime/correct.py`. **Open Q:** memory-rollback granularity; tiêu chí lên/xuống cấp degradation.

### B5 — Protected Memory + Provenance (chống T5)
- Mỗi entry lịch sử kèm **content-hash** + nhãn **provenance** (user/tool/system/model — nâng A2).
- Giám sát ghi bất thường: nếu tỷ lệ ghi **không từ hệ thống** vượt ngưỡng ⇒ ghi nhận violation (feed vào Entropy Monitor).
- **Lives in:** `runtime/memory.py`. **Open Q:** ngưỡng ghi bất thường; store backend (SQLite vs jsonl).

### B6 — Inter-Layer Feedback (hệ phản ứng động)
- **L1→L2 (escalate):** input nghi injection hoặc provenance=untrusted ⇒ nâng Verify ≥ Tier 2.
- **L2→L4 (action):** "INJECTION confirmed" ⇒ Rollback ngay.
- **L4→L3 (thắt):** degradation tăng ⇒ kéo trần đặc quyền xuống.
- **L4→L2 (phục hồi):** sau **5 bước an toàn liên tiếp** ⇒ giảm degradation + nới Verify để tối ưu hiệu năng.
- **Lives in:** `runtime/orchestrator.py` (state machine). Cần đủ L1–L4 mới ráp được.

---

## 4. Threat coverage
| Threat | Cơ chế chặn |
|---|---|
| Indirect Prompt Injection (tool-output) | L1 re-sanitize output trước khi vào memory (Bước 6) |
| T4 Tool-Description Injection | HMAC-SHA256 tool-desc (L3) |
| T5 Memory Corruption | Protected memory: content-hash + provenance + ghi-bất-thường (B5) |
| Privilege escalation / agent bị chiếm | Capability token TTL/max-call + degradation (L3/L4) |
| Vòng lặp lỗi / hành vi bất ổn | Entropy monitor bypass fast-path (A1→L2) + step-budget |

---

## 5. Phân phase cho SDD
1. **B0 Execution loop** — chốt engine (A vs B); dựng chokepoint + confined tools. *RD đầy đủ (quyết định API key + kiến trúc).*
2. **B3 L3 CONSTRAIN + B1 L1 INFORM** — gate quyền + khử khuẩn (chạy được sớm, giá trị bảo mật cao nhất).
3. **B2 L2 VERIFY** — Rule→Judge→Causal + entropy bypass.
4. **B4 L4 CORRECT** — rollback gồm memory + degradation.
5. **B5 Protected Memory** — song song từ B0.
6. **B6 Inter-layer feedback** — ráp cuối khi đủ L1–L4.

*Mỗi item = 1 vòng SDD riêng (add dần). Toàn bộ Nhóm B cần RD đầy đủ vì có quyết định/đánh đổi.*

---

## 6. Quyết định cần chốt trước khi SDD Nhóm B
| # | Quyết định | Ghi chú |
|---|---|---|
| D1 | Engine B0: bọc-codex (no key) hay anthropic-loop (per-tool, cần key) | SAFEHARNESS đầy đủ ⇒ anthropic-loop |
| D2 | Có dùng API key + chấp nhận cost không | Điều kiện tiên quyết của (B) |
| D3 | Model cho Judge/semantic-filter | vd haiku cho rẻ, opus cho chuẩn |
| D4 | Memory store backend | jsonl (đơn giản) vs SQLite (truy vấn) |
| D5 | Nơi giữ HMAC key + capability secret | `.env`, không commit |

---

## 7. Routing (CLAUDE.md)
- RD/SD/BD + review: Opus main session.
- Implement + test: Codex.
- Search/verify rộng: Sonnet subagent.

---
*Opus Harness — SAFEHARNESS Group B Design v1 | 2026-06-28*
