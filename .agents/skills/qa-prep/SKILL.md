---
name: qa-prep
description: Use before or during implementation to create a QA test plan from TODO, Plan, and Intent.
---

# QA Preparation

This skill converts design intent into testable quality conditions before implementation goes too far.

## Trigger Conditions

Use this skill for:

- `Size >= M`
- `Risk >= Medium`
- Bug tasks with regression risk
- Refactors that need behavior-preservation checks
- Intentional omissions recorded as design decisions
- Security / auth / privacy / payment / data safety / migration changes
- CI / validator / Skill / agent workflow / documentation rule changes

## Required Procedure

1. Read the TODO task.
2. Read the Plan.
3. Read the Intent.
4. Extract the design decisions that must be preserved.
5. Confirm or strengthen Acceptance Criteria.
6. Create Intent-derived Invariants.
7. Write Risk Assessment.
8. Build the Test Matrix.
9. Assign each AC / INV to automated tests, manual QA, validator, static check, or diff review.
10. Create or update `_docs/qa/<Area>/<slug>/test-plan.md`.
11. Update the TODO task's `QA:` field.

## Rules

- Do not make a test plan that only mirrors implementation details.
- Do not push everything into manual QA when automated checks are feasible.
- If a check is deferred, write the reason.
- For High / Critical risk, include rollback / recovery / data safety / security checks.
- For agent workflow changes, include agent misbehavior checks.

## Output

The QA test plan must include:

- Source of Intent
- Quality Goal
- Acceptance Criteria
- Intent-derived Invariants
- Risk Assessment
- Test Strategy
- Test Matrix
- Manual QA Checklist
- Regression Checklist
- Out of Scope
- Open Questions

## Example Test Matrix Rows

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
|---|---|---|---|---|---|---|
| AC-001 | TODO | Size >= M tasks require Plan / Intent / QA. | validator | `deno run --allow-read scripts/validate-todo.mjs` | Invalid task without QA fails validation. | planned |
| INV-001 | intent | QA docs must not be archived. | validator | `deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs` | `_docs/archives/qa/**` is rejected. | planned |
