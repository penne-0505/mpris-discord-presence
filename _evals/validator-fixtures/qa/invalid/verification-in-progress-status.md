---
title: Fixture QA verification in progress status
status: active
draft_status: n/a
qa_status: in-progress
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

# Fixture QA verification in progress status

## Summary

This fixture must fail because a verification record with a verdict cannot use `qa_status: in-progress`.

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/invalid/verification-in-progress-status.md` | FAIL | Completed verification cannot remain in progress. |

## Automated Test Results

- AC-001: In-progress verification status is expected to fail.

## Manual QA Results

- None

## Acceptance Criteria Coverage

- AC-001: Covered by in-progress status fixture.

## Invariant Coverage

- INV-001: Covered by in-progress status fixture.

## Deferred / Not Covered

- None

## Residual Risks

None

## Follow-up TODOs

- None
