---
title: Fixture QA status verdict mismatch
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-05-25
updated_at: 2026-05-25
references:
  - "_docs/qa/Workflow/incremental-adoption-scope/test-plan.md"
  - "_docs/intent/Workflow/incremental-adoption-scope/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/qa/Workflow/incremental-adoption-scope/verification.md"
---

# Fixture QA status verdict mismatch

## Summary

This fixture must fail because `qa_status: verified` conflicts with `Verdict: FAIL`.

## Verification Verdict

Verdict: FAIL

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/invalid/status-verdict-mismatch.md` | FAIL | The mismatch must be rejected. |

## Automated Test Results

- AC-001: Mismatch fixture is expected to fail.

## Manual QA Results

- None

## Acceptance Criteria Coverage

- AC-001: Covered by mismatch fixture.

## Invariant Coverage

- INV-001: Covered by mismatch fixture.

## Deferred / Not Covered

- None

## Residual Risks

- Incorrectly accepting this fixture would make verification evidence unreliable.

## Follow-up TODOs

- Template-Test-99: [Test] Keep qa_status / Verdict mismatch fixture active.
