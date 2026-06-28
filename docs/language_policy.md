# Language Policy — Ontology, RKB, BD Output, and Creator Notes

> Scope: language usage policy for the BD Chunk Project.  
> Purpose: define where to use English, Japanese, Vietnamese, and Vietnamese without diacritics.

---

## 1. Core policy

Use a hybrid language model:

```text
English / ASCII = machine control
Japanese = business meaning and client-facing output
Vietnamese = internal creator notes and review support
Vietnamese without diacritics = quick internal note only, never source of truth
```

Short rule:

```text
IDs and enum values use English ASCII.
Business terms and BD outputs use Japanese.
Creator notes may use Vietnamese.
Vietnamese no-diacritic notes are allowed only as non-authoritative internal notes.
Creator notes must never override source facts.
```

---

## 2. Language by layer

| Layer | Language | Example |
|---|---|---|
| ID / enum / schema key | English ASCII | `EXCEPTION_RULE`, `source_label`, `range_a1` |
| Ontology code | English ASCII | `BUSINESS_RULE`, `STATE_TRANSITION` |
| Domain code | English/Romaji ASCII | `KESHI`, `APPROVAL`, `BILLING` |
| Entity ID | English/Romaji ASCII | `ENT-KESHI-INVOICE_NO` |
| Entity business name | Japanese | `請求番号`, `売掛明細`, `消込済` |
| Requirement statement | Japanese | `金額が不一致の場合...` |
| Final BD output | Japanese | `対象明細を手動確認一覧に表示する。` |
| Official search/index text | Japanese-heavy | `金額 不一致 手動確認 売掛金消込` |
| Internal creator note | Vietnamese with diacritics | `Cần hỏi lại BA vì đây có thể là scope change.` |
| Quick scratch note | Vietnamese without diacritics | `Can hoi lai BA vi co the la scope change.` |
| Agent/tool prompt | English control + Japanese preservation rule | `Use English enum values. Preserve Japanese source text.` |

---

## 3. Machine-readable fields

These fields must use English/ASCII because they are stable across code, schemas, tools, CI/CD, and validators:

```text
id
enum
schema key
tool name
agent name
skill name
file path
artifact type
requirement type
source label
BD frame ID
domain code
entity ID
mapping ID
exception ID
```

Good:

```yaml
requirement_type: EXCEPTION_RULE
source_label: QA_CLARIFICATION
target_bd_frame_id: BD-EXCEPTION-001
domain_code: KESHI
entity_id: ENT-KESHI-INVOICE_NO
```

Bad:

```yaml
requirement_type: 例外処理
source_label: tra_loi_QA
entity_id: 請求番号
```

Better pattern:

```yaml
requirement_type: EXCEPTION_RULE
requirement_type_ja: 例外処理ルール
source_label: QA_CLARIFICATION
source_label_ja: QA回答による明確化
entity_id: ENT-KESHI-INVOICE_NO
entity_name_ja: 請求番号
```

---

## 4. Japanese business fields

Japanese must be preserved for business meaning because source documents and final BD documents are Japanese.

Use Japanese for:

```text
raw_text_ja
normalized_text_ja
requirement_statement_ja
bd_output_ja
business term canonical names
Japanese aliases
Japanese examples
Japanese search keywords
client-facing descriptions
```

Example:

```json
{
  "raw_text_ja": "差額あり | 金額が不一致 | 手動確認一覧に表示",
  "normalized_text_ja": "金額が不一致の場合、対象明細を手動確認一覧に表示する。",
  "requirement_statement_ja": "消込判定処理が売掛明細を評価する時、金額が不一致の場合、売掛金消込システムは対象明細を手動確認一覧に表示する。"
}
```

Rule:

```text
Do not translate Japanese business terms into English in final BD output unless explicitly required.
```

---

## 5. Vietnamese creator notes

Vietnamese is allowed for the BD creator's internal review notes.

Use Vietnamese notes for:

```text
review comments
BA/PM follow-up notes
uncertainty explanations
implementation reminders
scope-change warnings
human decision rationale
```

Recommended field:

```json
{
  "creator_notes": {
    "note_vi": "Cần kiểm tra lại với BA vì nội dung này có thể là QA bổ sung scope.",
    "note_vi_ascii": "Can kiem tra lai voi BA vi noi dung nay co the la QA bo sung scope.",
    "authoritative": false,
    "visibility": "internal",
    "created_by": "bd_creator",
    "created_at": "2026-06-28T10:00:00+09:00"
  }
}
```

Rules:

```text
Vietnamese creator notes are internal review aids.
They are not source facts.
They must not override raw Japanese source text.
They must not directly generate Japanese BD output unless human-approved as a formal decision.
```

---

## 6. Vietnamese without diacritics

Vietnamese without diacritics is allowed only for quick internal scratch notes.

Allowed:

```json
{
  "creator_notes": {
    "note_vi_ascii": "Can hoi lai BA vi noi dung nay co the la QA bo sung scope.",
    "authoritative": false,
    "visibility": "internal"
  }
}
```

Not allowed:

```yaml
requirement_type: ngoai_le_xu_ly
source_label: tra_loi_QA
status: can_review
```

Reason:

```text
No-diacritic Vietnamese is ambiguous, weaker for search, unsuitable for formal documentation, and not stable enough for enum or workflow states.
```

If a note matters for audit or review, prefer Vietnamese with diacritics in `note_vi`.

---

## 7. Do not rely on YAML comments for important notes

YAML comments may be lost by parsers and are not reliable for audit trails.

Not recommended:

```yaml
# can check lai voi BA
requirement_type: EXCEPTION_RULE
```

Recommended:

```yaml
requirement_type: EXCEPTION_RULE
creator_notes:
  note_vi: "Cần check lại với BA."
  note_vi_ascii: "Can check lai voi BA."
  authoritative: false
  visibility: internal
```

Rule:

```text
YAML comments are for humans reading the file.
Structured note fields are for workflow, review, audit, and tooling.
```

---

## 8. Ontology pattern

Ontology files should use English/ASCII keys and Japanese business labels.

Example:

```yaml
requirement_types:
  EXCEPTION_RULE:
    label_ja: 例外処理ルール
    label_en: Exception Rule
    description_ja: >
      通常条件から外れる場合、エラー、不一致、差額、異常系などに対する
      システム動作を定義する要件。
    description_en: >
      Requirement defining system behavior for abnormal, mismatch, error,
      or exception conditions.
    default_bd_frames:
      - BD-EXCEPTION-001
    examples_ja:
      - 金額が不一致の場合、対象明細を手動確認一覧に表示する。
    keywords_ja:
      - 不一致
      - 差額
      - エラー
      - 異常
      - 例外
```

Rule:

```text
Ontology key = machine stable code.
Japanese label/description/keywords = business meaning and retrieval support.
English description = optional developer support.
```

---

## 9. Entity and domain pattern

Entity IDs should be English/Romaji IDs with Japanese canonical names.

```yaml
entities:
  ENT-KESHI-INVOICE_NO:
    domain_code: KESHI
    canonical_name_ja: 請求番号
    canonical_name_en: Invoice Number
    entity_type: DATA_ITEM
    aliases_ja:
      - 請求No
      - 請求Ｎｏ
      - 請求ID
    data_type_hint: string
```

Domain files should separate code and business name:

```yaml
domains:
  KESHI:
    name_ja: 売掛金消込
    name_en: Accounts Receivable Clearing
    aliases_ja:
      - 消込
      - 入金消込
      - 売掛消込
```

RKB item should store both:

```json
{
  "domain_code": "KESHI",
  "domain_name_ja": "売掛金消込"
}
```

---

## 10. BD frame pattern

BD frame IDs should be English/ASCII. BD section titles should be Japanese.

```yaml
bd_frames:
  BD-EXCEPTION-001:
    frame_type: EXCEPTION
    title_ja: 例外処理
    title_en: Exception Handling
    accepted_requirement_types:
      - EXCEPTION_RULE
```

Final BD output should use Japanese titles and Japanese body text:

```md
## 例外処理

- 金額が不一致の場合、対象明細を手動確認一覧に表示する。  
  Source: `qa_keshikomi.xlsx / QA票!B13:E13`  
  RKB: `RKB-KESHI-EXC-002`
```

---

## 11. Search and index policy

Official search text should be Japanese-heavy because source documents and BD output are Japanese.

```json
{
  "rkb_id": "RKB-KESHI-EXC-002",
  "text_for_keyword_index": "売掛金消込 金額 不一致 差額 手動確認一覧 例外処理 QA回答",
  "text_for_embedding": "売掛金消込業務において、金額が不一致の場合、対象明細を手動確認一覧に表示する例外処理。",
  "keywords_ja": ["金額不一致", "差額", "手動確認", "例外処理"],
  "internal_keywords_vi": ["ngoại lệ", "cần review", "hỏi BA"]
}
```

Rules:

```text
Japanese terms drive official retrieval.
Vietnamese terms may support creator search.
Vietnamese terms must not affect official BD generation unless human-approved.
```

---

## 12. Agent prompt rule

Agent/tool prompts may use English for control instructions.

Required prompt rule:

```text
Use English enum values for ontology codes.
Preserve Japanese source text.
Generate requirement_statement_ja in natural Japanese.
Do not translate Japanese business terms into English in final BD output.
Creator notes in Vietnamese are internal review aids only.
Creator notes must not be treated as source facts.
Creator notes must not be used to generate Japanese BD output unless explicitly approved by a human.
```

---

## 13. Field naming convention

Use suffixes to avoid mixing languages in one field.

```text
*_ja       Japanese official business text
*_en       English support label/description
*_vi       Vietnamese internal note with diacritics
*_vi_ascii Vietnamese internal no-diacritic quick note
*_code     stable machine code
*_id       stable machine ID
```

Rule:

```text
Do not mix Japanese, English, and Vietnamese in the same field unless the field is explicitly free-text and non-authoritative.
```

---

## 14. Validation rules

Validators should enforce:

```text
[ ] enum values are English/ASCII controlled values
[ ] IDs match naming rules
[ ] Japanese source text is preserved in *_ja fields
[ ] creator_notes.authoritative is false by default
[ ] Vietnamese notes cannot promote an item to RKB_READY
[ ] Vietnamese notes cannot override source_label, requirement_type, or source provenance
[ ] final BD output is generated from RKB source facts, not creator notes
```

Valid example:

```json
{
  "requirement_type": "EXCEPTION_RULE",
  "requirement_type_ja": "例外処理ルール"
}
```

---

## 15. Final decision

The project uses this language policy:

```text
English/ASCII is the control language.
Japanese is the business language.
Vietnamese is the creator support language.
Vietnamese without diacritics is allowed only as a non-authoritative quick note.
```

Final rule:

```text
Official facts come from source documents and approved RKB fields.
Creator notes help humans review the work.
Creator notes are never the source of truth unless explicitly converted into an approved decision with provenance.
```
