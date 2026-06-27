# Chunking Strategy — Raw Input to Requirement Knowledge Base

> Scope: this document defines the chunking strategy from raw input files to the Requirement Knowledge Base (RKB).  
> Out of scope: BD mapping and BD patch generation. Those steps happen after RKB readiness.

---

## 1. Goal

The goal of chunking is not simply to split text into small pieces for RAG.

The goal is to transform raw project materials into **traceable, validated, semantically labeled requirement knowledge items** that are safe to store in the Requirement Knowledge Base.

```text
Raw Input
→ File Registry
→ Source Units
→ Traceable Chunks
→ Normalized Requirement Candidates
→ Ontology-Labeled RKB Items
→ RKB Ready for Retrieval / BD Mapping
```

The key principle:

```text
No raw text enters RKB without provenance.
No chunk becomes a requirement without validation.
No pending or inferred item becomes fact automatically.
```

---

## 2. Design principles

### 2.1 Provenance first

Every chunk must be traceable to its original source.

For Excel:

```text
workbook_name
workbook_sha256
sheet_name
range_a1
source_granularity = row_range | block_range | cell_range_optional
```

For Word / Markdown:

```text
document_name
document_sha256
heading_path
paragraph_index or line_range
```

For PDF:

```text
file_name
file_sha256
page_number
text_block_id or bbox_optional
```

If provenance is missing, the item must go to `exceptions` and must not enter RKB.

---

### 2.2 Deterministic parser before AI

The parser must produce source locators before any LLM processing.

Correct:

```text
openpyxl reads workbook/sheet/range
→ source unit contains QA票!B12:E12
→ LLM may classify or normalize text later
```

Incorrect:

```text
convert Excel to Markdown
→ ask LLM to guess original range
→ store guessed range in RKB
```

Source range must never be inferred by LLM.

---

### 2.3 Chunk by business boundary, not only token size

Generic RAG often chunks by token count. This project should chunk by business structure first.

Priority order:

```text
1. Source structure
2. Business boundary
3. Requirement behavior boundary
4. Token budget
```

Example:

```text
One Excel QA row that describes one rule = one source unit / one chunk.
One RD section that describes one screen behavior = one chunk.
One large RD section with multiple behaviors = split into multiple candidate chunks.
```

---

### 2.4 Parent-child hierarchy

Chunks should preserve hierarchy.

```text
Document
→ Section / Sheet
→ Table / Block
→ Row / Paragraph
→ Optional Cell / Sentence
```

For Excel:

```text
workbook → sheet → table/block → row → cell_optional
```

For RD documents:

```text
document → heading → subsection → paragraph/block → sentence_optional
```

MVP should retrieve at row/block level, but store parent context to support better interpretation.

---

### 2.5 Separate source text, normalized text, and embedding text

A chunk should not have only one text field.

Use separate fields:

```text
raw_text           = exact parsed text from source
normalized_text    = cleaned text preserving meaning
contextual_text    = text enriched with source/business context for search
requirement_text   = EARS/RKB-ready requirement statement
```

Important:

```text
contextual_text can improve retrieval.
It must not create new facts.
Only raw_text + source are ground truth.
```

---

## 3. Chunking lifecycle

Each item goes through this lifecycle:

```text
RAW_REGISTERED
→ PARSED_TO_SOURCE_UNIT
→ SOURCE_VALIDATED
→ CHUNKED
→ NORMALIZED
→ CLASSIFIED
→ ONTOLOGY_LABELED
→ RKB_CANDIDATE
→ RKB_READY
```

If any gate fails:

```text
→ EXCEPTION_QUEUE
```

Possible review statuses:

```text
Draft
Needs_Review
Approved
Rejected
Superseded
Deprecated
```

---

## 4. Stage 1 — Raw file registry

### 4.1 Purpose

Register every raw input file before parsing.

### 4.2 Output file

```text
data/index/file_registry.jsonl
```

### 4.3 Required fields

```json
{
  "file_id": "sha256:abc123",
  "file_name": "qa_keshikomi.xlsx",
  "file_path": "data/raw/qa_keshikomi.xlsx",
  "file_type": "excel",
  "source_kind": "QA",
  "file_sha256": "abc123",
  "ingested_at": "2026-06-27T10:00:00+09:00",
  "parser_hint": "openpyxl",
  "status": "RAW_REGISTERED"
}
```

### 4.4 Source kind enum

```text
RD
QA
LEGACY
MEETING_NOTE
BUSINESS_FLOW
EXISTING_BD
TECHNICAL_NOTE
UNKNOWN
```

---

## 5. Stage 2 — Source unit extraction

### 5.1 Source unit definition

A source unit is the smallest deterministic unit parsed from raw input with source location.

It is not necessarily a final requirement.

```text
Source Unit = raw text + deterministic source locator
```

### 5.2 Output file

```text
data/outputs/source_units.jsonl
```

---

## 6. Excel chunking strategy

Excel is the highest priority source type for this MVP because QA sheets often contain requirement clarifications.

### 6.1 Excel hierarchy

```text
Workbook
→ Sheet
→ Logical table/block
→ Row
→ Cell optional
```

### 6.2 Default chunking rule

Default:

```text
1 non-empty business row = 1 source unit
```

Example:

```text
qa_keshikomi.xlsx / QA票!B13:E13
```

```json
{
  "unit_id": "SRC-QA-00013",
  "file_id": "sha256:abc123",
  "source_type": "excel",
  "raw_text": "差額あり | 金額が不一致 | 手動確認一覧に表示 | 差額理由を確認",
  "source": {
    "workbook_name": "qa_keshikomi.xlsx",
    "workbook_sha256": "abc123",
    "sheet_name": "QA票",
    "range_a1": "QA票!B13:E13",
    "source_granularity": "row_range"
  },
  "status": "PARSED_TO_SOURCE_UNIT"
}
```

### 6.3 Block-level chunks

Use block-level chunking when one logical table section spans multiple rows and one row alone is not meaningful.

Example:

```text
QA票!B20:H30 = decision table for clearing result
```

Output:

```json
{
  "unit_id": "SRC-QA-BLOCK-001",
  "source_type": "excel",
  "raw_text": "消込判定条件テーブル ...",
  "source": {
    "workbook_name": "qa_keshikomi.xlsx",
    "sheet_name": "QA票",
    "range_a1": "QA票!B20:H30",
    "source_granularity": "block_range"
  },
  "artifact_hint": "DECISION_TABLE"
}
```

### 6.4 Cell-level trace

Cell-level trace is optional and should not be mandatory for MVP.

Use cell-level metadata only for:

```text
- high-risk fields
- debugging
- conflicting cells
- generated BD wording validation
```

MVP quality bar:

```text
100% Excel-derived chunks traceable to workbook / sheet / row-range or block-range.
```

### 6.5 Excel warnings

Parser should capture warnings:

```text
merged_cells_detected
hidden_rows_detected
hidden_columns_detected
formula_cells_detected
empty_required_columns
multi_behavior_row
```

Warnings do not always block ingestion, but they should be stored.

---

## 7. Word / Markdown chunking strategy

### 7.1 Hierarchy

```text
Document
→ Heading path
→ Section block
→ Paragraph
→ Sentence optional
```

### 7.2 Default chunking rule

Default:

```text
1 heading section or paragraph block = 1 source unit
```

Split further if the block contains multiple independent system behaviors.

### 7.3 Example

```json
{
  "unit_id": "SRC-RD-003-002",
  "file_id": "sha256:rd999",
  "source_type": "markdown",
  "raw_text": "ユーザーが申請を送信した場合、システムは入力項目をチェックし、不備がなければ申請ステータスを承認待ちに更新する。",
  "source": {
    "document_name": "RD_v1.md",
    "document_sha256": "rd999",
    "heading_path": "3. 申請登録 > 3.2 登録処理",
    "line_range": "L120-L128",
    "source_granularity": "section_block"
  }
}
```

---

## 8. PDF chunking strategy

PDF is lower priority for MVP because precise layout extraction is harder.

Recommended rule:

```text
Use PDF only when text extraction and page provenance are reliable.
```

Required provenance:

```text
file_name
file_sha256
page_number
text_block_id or line_range if available
```

If PDF contains tables or diagrams, mark:

```text
needs_manual_review = true
```

Do not use OCR-derived text as high-authority source unless reviewed.

---

## 9. Traceable chunk construction

### 9.1 Chunk definition

A traceable chunk is a validated source unit transformed into a cleaner business chunk.

```text
Traceable Chunk = source unit + normalized text + content hash + provenance
```

### 9.2 Output file

```text
data/outputs/traceable_chunks.jsonl
```

### 9.3 Required fields

```json
{
  "chunk_id": "CHK-KESHI-001",
  "source_unit_ids": ["SRC-QA-00013"],
  "raw_text": "差額あり | 金額が不一致 | 手動確認一覧に表示 | 差額理由を確認",
  "normalized_text_ja": "金額が不一致の場合、対象明細を手動確認一覧に表示し、差額理由を確認する。",
  "content_hash": "sha256:def456",
  "source": {
    "workbook_name": "qa_keshikomi.xlsx",
    "workbook_sha256": "abc123",
    "sheet_name": "QA票",
    "range_a1": "QA票!B13:E13",
    "source_granularity": "row_range"
  },
  "status": "CHUNKED"
}
```

### 9.4 Chunk ID strategy

Chunk ID should be deterministic.

Recommended:

```text
chunk_id = CHK-<domain_or_file_hint>-<short_hash>
short_hash = hash(file_id + source_locator + normalized_text)
```

Human-readable examples:

```text
CHK-KESHI-001
CHK-APPROVAL-004
CHK-QA-7F91A2
```

---

## 10. Normalization strategy

### 10.1 Normalization allowed

Allowed:

```text
- trim whitespace
- join row cells using separators
- remove duplicated headers
- normalize Japanese punctuation
- preserve domain terms
- rewrite fragmented table text into one readable sentence
```

### 10.2 Normalization not allowed

Not allowed:

```text
- add new business conditions
- infer missing status
- turn pending into confirmed requirement
- remove source uncertainty
- merge unrelated behaviors into one fact
```

### 10.3 Ambiguous expressions

Mark these as ambiguity flags:

```text
別途確認
未定
必要に応じて
適切に
原則として
できるだけ
なるべく
いい感じに
柔軟に
```

Example:

```json
{
  "ambiguity_flags": ["別途確認"],
  "review_required": true,
  "allow_rkb_ready": false
}
```

---

## 11. Requirement candidate extraction

A chunk may or may not contain a requirement.

### 11.1 Extract only actionable system behavior

Good candidate:

```text
金額が不一致の場合、システムは対象明細を手動確認一覧に表示する。
```

Bad candidate:

```text
ユーザーが使いやすいようにする。
```

### 11.2 Candidate types

```text
SYSTEM_BEHAVIOR
BUSINESS_RULE
VALIDATION
EXCEPTION
STATE_TRANSITION
DATA_DEFINITION
REFERENCE_ONLY
PENDING_DECISION
NOT_REQUIREMENT
```

### 11.3 Multiple behaviors

If one source unit contains multiple behaviors, create multiple candidates but keep the same source.

Example:

```text
入力チェックを行い、問題がなければ登録し、問題がある場合はエラーを表示する。
```

Split into:

```text
Candidate 1: input validation
Candidate 2: successful registration
Candidate 3: error display
```

All candidates keep the same source reference.

---

## 12. Ontology labeling before RKB

### 12.1 Purpose

Ontology labeling determines what the chunk means and whether it is eligible for RKB.

It answers:

```text
What type of requirement is this?
What source authority does it have?
Which domain does it belong to?
Is it pending, conflicting, or inferred?
Which BD frame might it later map to?
```

### 12.2 Labels to attach

```json
{
  "source_label": "QA_CLARIFICATION",
  "authority_rank": 2,
  "requirement_type": "EXCEPTION_RULE",
  "ears_type": "Complex",
  "domain": "売掛金消込",
  "business_entities": ["Payment", "Invoice"],
  "affected_artifacts": ["ManualReviewList"],
  "target_bd_frame_hint": "BD-EXCEPTION-001"
}
```

### 12.3 Labeling rules

Rule examples:

```text
If text contains 不一致 / 差額 / エラー / 失敗:
  requirement_type = EXCEPTION_RULE

If text contains 入力 / 必須 / 桁数 / 形式 / チェック:
  requirement_type = VALIDATION_RULE

If text contains ステータス / 状態 / 承認待ち / 完了 / 却下:
  requirement_type = STATE_TRANSITION

If text contains バッチ / 日次 / 月次 / 定期:
  requirement_type = BATCH_PROCESS

If text contains API / リクエスト / レスポンス:
  requirement_type = API_BEHAVIOR
```

If uncertain:

```text
requirement_type = NEEDS_REVIEW
```

---

## 13. EARS normalization before RKB

EARS normalization is used only for behavior requirements.

### 13.1 Required fields

```json
{
  "ears_type": "Complex",
  "when_trigger": "消込判定処理が売掛明細を評価する",
  "if_condition": "金額が不一致である",
  "system_name": "売掛金消込システム",
  "system_response": "対象明細を手動確認一覧に表示する"
}
```

### 13.2 Japanese requirement statement

```text
消込判定処理が売掛明細を評価する時、金額が不一致の場合、売掛金消込システムは対象明細を手動確認一覧に表示する。
```

### 13.3 Do not force EARS for all items

Do not force EARS when the source is:

```text
- data dictionary
- decision table
- state matrix
- non-functional requirement
- reference-only legacy behavior
```

Use artifact types instead:

```text
EARS_REQUIREMENT
DECISION_TABLE_REFERENCE
STATE_MATRIX_REFERENCE
DATA_DEFINITION
REFERENCE_ONLY
```

---

## 14. Decision table and state matrix chunks

### 14.1 Decision table chunk

Use when:

```text
many conditions → decision/action
```

Store as:

```json
{
  "artifact_type": "DECISION_TABLE_REFERENCE",
  "artifact_id": "DT-KESHI-001",
  "requirement_statement_ja": "消込判定処理が入金明細を評価する時、売掛金消込システムは Decision Table DT-KESHI-001 に従って消込処理区分を判定する。",
  "source": {
    "workbook_name": "qa_keshikomi.xlsx",
    "sheet_name": "QA票",
    "range_a1": "QA票!B20:H30"
  }
}
```

### 14.2 State matrix chunk

Use when:

```text
current state + event → next state + action
```

Store as:

```json
{
  "artifact_type": "STATE_MATRIX_REFERENCE",
  "artifact_id": "ST-APP-001",
  "requirement_statement_ja": "承認処理が実行される時、購買申請システムは State Matrix ST-APP-001 に従って申請ステータスを更新する。",
  "source": {
    "workbook_name": "approval_rules.xlsx",
    "sheet_name": "状態遷移",
    "range_a1": "状態遷移!B5:F20"
  }
}
```

---

## 15. RKB item creation

### 15.1 RKB item definition

An RKB item is a chunk that has passed traceability validation and semantic eligibility checks.

```text
RKB Item = traceable chunk + normalized requirement + ontology + status
```

### 15.2 Output file

```text
data/outputs/rkb_items.jsonl
```

### 15.3 RKB item schema

```json
{
  "rkb_id": "RKB-KESHI-002",
  "chunk_id": "CHK-KESHI-002",
  "artifact_type": "EARS_REQUIREMENT",
  "raw_text_ja": "金額が不一致の場合、手動確認一覧に表示する",
  "normalized_text_ja": "金額が不一致の場合、対象明細を手動確認一覧に表示する。",
  "requirement_statement_ja": "消込判定処理が売掛明細を評価する時、金額が不一致の場合、売掛金消込システムは対象明細を手動確認一覧に表示する。",
  "ontology": {
    "source_label": "QA_CLARIFICATION",
    "authority_rank": 2,
    "requirement_type": "EXCEPTION_RULE",
    "ears_type": "Complex",
    "domain": "売掛金消込",
    "business_entities": ["Payment", "Invoice"],
    "affected_artifacts": ["ManualReviewList"],
    "target_bd_frame_hint": "BD-EXCEPTION-001"
  },
  "source": {
    "workbook_name": "qa_keshikomi.xlsx",
    "workbook_sha256": "abc123",
    "sheet_name": "QA票",
    "range_a1": "QA票!B13:E13"
  },
  "status": "Draft",
  "confidence": "high",
  "conflict_flag": false,
  "review_required": false,
  "lifecycle_status": "RKB_READY"
}
```

---

## 16. RKB readiness gates

A candidate can become RKB-ready only if all gates pass.

### Gate 1 — Provenance gate

```text
[ ] source exists
[ ] file hash exists
[ ] source locator exists
[ ] Excel has workbook/sheet/range
[ ] range granularity is row_range or block_range
```

### Gate 2 — Content gate

```text
[ ] raw_text is not empty
[ ] normalized_text is not empty
[ ] content_hash exists
[ ] not pure header/footer/noise
```

### Gate 3 — Semantic gate

```text
[ ] requirement_type exists
[ ] source_label exists
[ ] artifact_type exists
[ ] if behavior requirement, requirement_statement_ja exists
```

### Gate 4 — Risk gate

Block from RKB-ready or mark Needs_Review if:

```text
[ ] PENDING_DECISION
[ ] TECHNICAL_INFERENCE
[ ] conflict_flag = true
[ ] ambiguity_flags not empty
[ ] multiple behaviors not split
[ ] low confidence
```

### Gate 5 — ID integrity gate

```text
[ ] rkb_id unique
[ ] chunk_id exists
[ ] source_unit_ids exist
[ ] no duplicate active item with same content_hash + source
```

---

## 17. Contextual text for search

Before indexing, create `contextual_text`.

Example:

```text
Domain: 売掛金消込
Source: QA_CLARIFICATION
Artifact: EXCEPTION_RULE
Text: 金額が不一致の場合、対象明細を手動確認一覧に表示する。
```

Use this for BM25/vector indexing, but do not treat added context as source fact.

Recommended fields:

```json
{
  "text_for_keyword_index": "金額 不一致 手動確認 売掛金消込 QA_CLARIFICATION EXCEPTION_RULE",
  "text_for_embedding": "売掛金消込業務の例外処理。金額が不一致の場合、対象明細を手動確認一覧に表示する。",
  "source_fact_text": "金額が不一致の場合、対象明細を手動確認一覧に表示する。"
}
```

---

## 18. Index outputs before BD mapping

After RKB creation, build indexes for retrieval.

### 18.1 Provenance index

```text
data/index/provenance_index.jsonl
```

```json
{
  "rkb_id": "RKB-KESHI-002",
  "chunk_id": "CHK-KESHI-002",
  "file_id": "sha256:abc123",
  "source_ref": "qa_keshikomi.xlsx / QA票!B13:E13",
  "source_label": "QA_CLARIFICATION",
  "lifecycle_status": "RKB_READY"
}
```

### 18.2 Keyword index / BM25 input

```text
data/index/keyword_index.jsonl
```

```json
{
  "index_id": "KW-KESHI-002",
  "rkb_id": "RKB-KESHI-002",
  "text_for_keyword_index": "金額 不一致 手動確認 売掛金消込 QA_CLARIFICATION EXCEPTION_RULE",
  "keywords": ["金額不一致", "手動確認", "売掛金消込", "例外処理"]
}
```

### 18.3 Semantic index manifest

```text
data/index/semantic_index_manifest.jsonl
```

```json
{
  "index_id": "SEM-KESHI-002",
  "rkb_id": "RKB-KESHI-002",
  "text_for_embedding": "売掛金消込業務の例外処理。金額が不一致の場合、対象明細を手動確認一覧に表示する。",
  "embedding_status": "not_generated",
  "vector_ref": null
}
```

---

## 19. Exception queue

Any failed item should be written to:

```text
data/outputs/exceptions.jsonl
```

Example:

```json
{
  "exception_id": "EXC-001",
  "source_unit_id": "SRC-QA-00021",
  "reason": "PENDING_DECISION detected",
  "raw_text": "処理方式は別途確認",
  "source_ref": "qa_keshikomi.xlsx / QA票!B21:E21",
  "recommended_action": "Human review required before RKB approval"
}
```

---

## 20. Output contract before BD mapping

Before BD mapping starts, the pipeline must produce:

```text
data/index/file_registry.jsonl
data/outputs/source_units.jsonl
data/outputs/traceable_chunks.jsonl
data/outputs/rkb_items.jsonl
data/index/provenance_index.jsonl
data/index/keyword_index.jsonl
data/index/semantic_index_manifest.jsonl
data/outputs/exceptions.jsonl
```

BD mapping should consume only:

```text
RKB-ready items
+ provenance index
+ ontology labels
+ retrieval indexes
```

BD mapping should not consume raw files directly.

---

## 21. Acceptance criteria

The chunking strategy is implemented correctly when:

```text
[ ] Every raw file has a file registry record.
[ ] Every Excel source unit has workbook/sheet/range.
[ ] Every traceable chunk has content_hash and source reference.
[ ] Every RKB item has ontology labels.
[ ] Pending and inferred items are not marked RKB_READY automatically.
[ ] BM25 index can search RKB items by exact Japanese terms.
[ ] Semantic index manifest exists even if embeddings are not generated yet.
[ ] Exceptions are written for invalid or ambiguous items.
[ ] BD mapping can run without reading raw files directly.
```

---

## 22. Final summary

```text
Chunking in this project means:
raw file fingerprinting,
deterministic source extraction,
traceable chunk construction,
normalization without inventing facts,
ontology labeling,
RKB readiness validation,
and index preparation before BD mapping.
```

Short version:

```text
Raw files are parsed into traceable chunks.
Traceable chunks are normalized and labeled.
Only validated, reviewable, source-backed items enter RKB.
BD mapping starts after RKB, never directly from raw files.
```
