---
title: Fixture QA missing test plan reference
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-05-25
updated_at: 2026-05-25
references:
  - "_docs/intent/Workflow/incremental-adoption-scope/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/qa/Workflow/incremental-adoption-scope/verification.md"
---

# Fixture QA missing test plan reference

## Summary

This fixture must fail because verification references omit the matching test-plan.

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `deno run --allow-read scripts/validate-qa.mjs --fixture _evals/validator-fixtures/qa/invalid/verification-missing-test-plan-reference.md` | FAIL | Missing test-plan reference must be rejected. |

## Automated Test Results

- AC-001: Missing test-plan reference is expected to fail.

## Manual QA Results

- None

## Acceptance Criteria Coverage

- AC-001: Covered by missing-reference fixture.

## Invariant Coverage

- INV-001: Covered by missing-reference fixture.

## Deferred / Not Covered

- None

## Residual Risks

None

## Follow-up TODOs

- None
