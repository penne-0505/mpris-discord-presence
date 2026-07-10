---
title: Fixture QA test plan
status: active
draft_status: n/a
qa_status: planned
risk: Medium
created_at: 2026-05-25
updated_at: 2026-05-25
references:
  - "_docs/plan/Workflow/incremental-adoption-scope/plan.md"
  - "_docs/intent/Workflow/incremental-adoption-scope/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/qa/Workflow/incremental-adoption-scope/test-plan.md"
---

# Fixture QA test plan

## Source of Intent

- Intent: `_docs/intent/Workflow/incremental-adoption-scope/decision.md`

## Quality Goal

Validate that a complete QA test-plan fixture passes.

## Acceptance Criteria

- AC-001: The fixture includes acceptance criteria.

## Intent-derived Invariants

- INV-001: QA docs must remain live quality records.

## Risk Assessment

Risk: Medium.

## Test Strategy

Use `validate-qa.mjs` in fixture mode.

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | fixture | Valid QA test-plan passes. | validator | `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/valid` | Validator exits 0. | planned |
| INV-001 | intent | QA docs are not archived. | validator | `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/valid` | Canonical QA path is accepted. | planned |

## Manual QA Checklist

- Confirm fixture content is intentionally minimal but substantive.

## Regression Checklist

- Confirm fixture mode does not read real TODO.md.

## Out of Scope

- Runtime browser testing.

## Open Questions

- None
