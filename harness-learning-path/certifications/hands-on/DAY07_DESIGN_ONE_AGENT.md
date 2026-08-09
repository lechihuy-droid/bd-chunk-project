# DAY 7 — HANDS-ON 1: DESIGN ONE APPLICATION AGENT

> Integrated track: AI-103 + GH-300  
> Goal: convert certificate concepts into a concrete agent specification  
> Suggested capstone: RD Parser Agent

---

# 1. Session Outcome

By the end of Day 7, you should have one agent designed end-to-end **before writing implementation code**.

Deliverable:

```text
Agent Specification
├── Role
├── Goal
├── Input Contract
├── Output Contract
├── Model Requirements
├── Instructions
├── Tools
├── Knowledge
├── State
├── Memory
├── Guardrails
├── Evaluation
└── Failure / Review Policy
```

The purpose is to prove you understand the application agent independently from any specific SDK.

---

# 2. Why Start from the Contract

A common mistake is:

```text
Prompt first
→ keep tweaking
→ unclear output
→ downstream breaks
```

Preferred order:

```text
Business Goal
 ↓
Output Contract
 ↓
Input Contract
 ↓
Decision Boundary
 ↓
Tools / Knowledge
 ↓
Instructions
 ↓
Model Choice
```

The downstream consumer should be able to understand what this agent produces without reading the prompt.

---

# 3. Capstone Agent — RD Parser

## Business purpose

Convert a Requirement Document into small traceable requirement blocks that downstream validation/build steps can consume.

## Role

```text
RD Parser Agent
= requirement extraction specialist
```

## Goal

```text
Extract the smallest meaningful requirement units
while preserving source traceability and uncertainty.
```

---

# 4. Input Contract

Example conceptual input:

```yaml
RDParserInput:
  document_id: string
  document_content: document/reference
  metadata:
    title: string
    version: string
    source_uri: optional string
  parsing_scope: optional section/range
```

Questions:

- Is the entire document supplied or a reference to it?
- Is source metadata mandatory?
- Can the agent process only one section?
- What happens if the document is unreadable?

---

# 5. Output Contract

Conceptual output:

```yaml
RequirementBlock:
  id: string
  requirement_text: string
  original_text: string
  source_reference:
    document_id: string
    section: string
    page_or_location: optional string
  category: optional string
  confidence: optional number
  needs_review: boolean
  notes: optional string
```

The exact schema can change later. The important point is the contract semantics.

## Required semantic obligations

1. `requirement_text` must preserve the meaning of the source.
2. `original_text` must be traceable to the input document.
3. `source_reference` must identify where the requirement came from.
4. uncertain extraction must set `needs_review=true`.
5. the parser must not invent missing requirements.

---

# 6. Structural vs Semantic Validation

```text
Structural
- fields exist
- types are valid
- schema is valid

Semantic
- source reference is real
- original text matches source
- requirement meaning is preserved
- no unsupported requirement invented
```

This distinction maps directly to the AI-103 contract/validation mental model.

---

# 7. Agent vs Tool Boundary

Ask whether each capability requires autonomous reasoning.

### Candidate: read_document

```text
Need reasoning? no
Need autonomy? no
Result deterministic? mostly yes
```

Therefore:

> Tool, not agent.

### Candidate: split requirement semantics

```text
Need language reasoning? yes
Need interpretation? yes
Potential ambiguity? yes
```

Therefore:

> Good candidate for agent/model reasoning.

### Candidate: check required fields

Deterministic schema validation.

> Validator/function, not agent.

---

# 8. Tool Set

Minimal tool set:

```text
RD Parser Agent
├── read_document()
├── get_section()
└── locate_source()
```

Optional later:

```text
search_document()
retrieve_domain_rule()
submit_for_review()
```

For every tool define:

- purpose;
- input;
- output;
- permissions;
- error behavior;
- whether retry is safe.

---

# 9. Knowledge Decision

Do not automatically add RAG.

Decision tree:

```text
One small RD already available?
→ direct read may be sufficient

Many large RDs / changing corpus / enterprise standards?
→ retrieval/index may be justified
```

Document why the agent needs—or does not need—a knowledge layer.

---

# 10. State and Memory

Example state:

```yaml
RunState:
  current_document_id:
  current_section:
  extracted_blocks:
  unresolved_findings:
  status:
```

Memory is optional.

Question:

> Does the parser need to remember information across separate RD parsing runs?

If not, do not add persistent memory just because "agents have memory".

---

# 11. Guardrails

At minimum:

- never fabricate source text;
- never silently drop uncertain content;
- never overwrite original evidence;
- mark ambiguity for review;
- respect document access permissions.

Guardrails should connect to runtime behavior, not only prompt wording.

---

# 12. Evaluation

Define what "good" means before implementation.

Suggested dimensions:

```text
Requirement coverage
Source fidelity
Block granularity
Hallucination rate
Traceability completeness
Contract compliance
Human review rate
```

Example golden-case question:

> Given this source paragraph, did the agent identify all independent requirements and preserve evidence?

---

# 13. GH-300 Integration

Now switch perspective.

You are using a coding agent to implement the RD Parser Agent.

The coding-agent context should include:

```text
Agent specification
Output contract
Repository instructions
Existing project structure
Testing expectations
Security constraints
```

Do not ask:

> "Build me an AI agent."

Prefer:

> "Implement the supplied RDParser contract in the existing architecture; do not change public interfaces; add tests for traceability and unsupported requirement generation."

This is prompt + context engineering applied to software delivery.

---

# 14. Practical Exercise — Voice-First Mode

If no API is available, perform the session entirely through conversation.

### Step A
Explain the RD Parser goal in one sentence.

### Step B
Define its output contract verbally.

### Step C
Classify each capability as:

- agent reasoning;
- tool;
- deterministic validator;
- human review.

### Step D
State three guardrails.

### Step E
Define three evaluation criteria.

### Step F
Write one coding-agent instruction for implementing the specification later.

---

# 15. Review Scenarios

### Scenario 1
The parser receives a malformed source file.

Question: should the LLM reason around the corruption or should the runtime/tool return a controlled error?

Preferred: controlled tool/runtime error first.

### Scenario 2
A requirement sentence is ambiguous.

Preferred: extract with `needs_review=true`, preserving original evidence.

### Scenario 3
The parser invents a requirement that sounds reasonable but is absent from the RD.

Classification: semantic/evaluation failure, not schema failure.

---

# 16. Day 7 PASS Gate

Without notes, explain:

1. Why design output contract before prompt?
2. Which RD Parser responsibilities require reasoning?
3. Which responsibilities should remain deterministic?
4. Why does source traceability belong in the contract?
5. State vs memory for this agent.
6. When would RAG become justified?
7. Three guardrails.
8. Three evaluation metrics.
9. Difference between the RD Parser Agent and the coding agent that implements it.
10. What context should a coding agent receive?

## PASS

Pass at **8/10** plus a complete verbal agent specification.

---

# 17. Deliverable

Create or record:

```text
RD_PARSER_AGENT_SPEC
├── purpose
├── input contract
├── output contract
├── tool list
├── knowledge decision
├── state/memory decision
├── guardrails
├── evaluation criteria
└── implementation instruction
```

Next: Day 8 adds Tool + RAG + MCP around this agent.
