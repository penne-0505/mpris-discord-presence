---
title: Fixture QA archive path
status: active
draft_status: n/a
qa_status: planned
risk: Medium
created_at: 2026-05-25
updated_at: 2026-05-25
references:
  - "_docs/intent/Workflow/incremental-adoption-scope/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/archives/qa/Workflow/incremental-adoption-scope/test-plan.md"
---

# Fixture QA archive path

## Source of Intent

- Intent: `_docs/intent/Workflow/incremental-adoption-scope/decision.md`

## Quality Goal

This fixture must fail because QA docs are never archived.

## Acceptance Criteria

- AC-001: QA archive paths are rejected.

## Intent-derived Invariants

- INV-001: QA docs remain persistent live records.

## Risk Assessment

Risk: Medium.

## Test Strategy

Use `validate-qa.mjs` in fixture mode.

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | fixture | QA archive path fails. | validator | `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/invalid/qa-archive-path.md` | Validator exits non-zero. | planned |
| INV-001 | intent | QA docs must not be archived. | validator | `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/invalid/qa-archive-path.md` | `archives/qa` is rejected. | planned |

## Manual QA Checklist

- None

## Regression Checklist

- None

## Out of Scope

- Runtime QA.

## Open Questions

- None
