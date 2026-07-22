---
name: implementation-prep
description: Use before any implementation request that touches multiple files or requires TODO/document alignment.
---

# Implementation Preparation

This skill collects requirements, aligns them with repository documentation, and makes `TODO.md` the task source of truth before implementation begins.

## Preparation Flow

1. **Clarify the request.** Restate the goal, assumptions, and open questions.
2. **Document reconnaissance.** Read the relevant README, standards, plans, intents, QA docs, and workflow guides before editing code.
3. **TODO.md audit.** Confirm the task has `Size`, `Risk`, `Acceptance Criteria`, `Plan`, `Intent`, `QA`, and `Verification`.
4. **Risk gate.** If `Size >= M` or `Risk >= Medium`, run `docs-prep` and `qa-prep` before implementation.
5. **Plan synthesis.** Produce an implementation plan with user-visible changes, dependencies, verification steps, and unresolved questions.
6. **Share the plan.** Present the relevant docs, TODO entry, QA expectations, and blockers before touching implementation files.

## Before Implementation

- If `Size >= M` or `Risk >= Medium`, run `qa-prep`.
- Confirm Plan / Intent / QA exist.
- Confirm Acceptance Criteria are clear and use `AC-001` style IDs.
- Confirm the Test Matrix has at least one planned check for each core AC and each applicable INV.
- For Bug tasks, confirm regression test or no-test rationale is planned.
- For Refactor tasks, confirm behavior-preservation checks are planned.
- For Agent workflow / validator / CI / Skill / documentation rule changes, confirm agent misbehavior checks are planned.
- Plan to anchor non-obvious code to intent: where a deliberate decision (especially a why not or intentional omission) would read as missing or removable, leave a `// intent: DEC-00X (<Area>/<slug>) — <causal why>` comment. Use `// intent-invariant: INV-00X ...` only for a strict invariant. This is targeted, not blanket. See `quality_assurance.md` (intent ↔ code traceability).

## Document & TODO Strategy

- Treat documentation as the contract. Keep exact doc paths and sections handy.
- Use `TODO.md` as a living checklist, not as a history log.
- Use root-relative canonical paths for `Plan`, `Intent`, `QA`, and `Verification`.
- Do not start implementation for `Size >= M` or `Risk >= Medium` while `Intent` or `QA` is missing.

## Deliverables Before Implementation

- Written summary of docs read and assumptions.
- Updated or confirmed TODO entry.
- Implementation plan tied to Acceptance Criteria.
- QA prep status, including affected DEC review, planned AC checks, and any applicable INV checks.
- Open questions or blockers.

## Tracks

### Fast Track

For `Size XS/S` and `Risk Low` tasks:

- Use this skill alone.
- Plan / Intent / QA can be `None`.
- Before keeping them `None`, check intentional omission risk: if a future maintainer could mistake a deliberate limitation, unsupported path, or omission for missing work, record the reason in TODO Description, PR / commit notes, or escalate to docs-prep.
- Record intent in TODO, PR, commit, or a lightweight follow-up if needed.

### Standard Track

For `Size >= M`, `Risk >= Medium`, design-decision work, or intentional omission risk that affects future work:

- Use `docs-prep`.
- Use `qa-prep`.
- Follow `plan -> intent -> qa/test-plan -> implementation -> qa/verification`.
