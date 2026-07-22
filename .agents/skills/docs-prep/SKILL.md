---
name: docs-prep
description: Use after implementation-prep when the change is Size >= M, Risk >= Medium, or requires design decisions.
---

# Documentation Preparation

This skill prepares canonical documentation before substantial implementation work.

## When to Use

Use this skill for:

- `Size >= M`
- `Risk >= Medium`
- Architecture decisions
- Intentional omissions that future maintainers could mistake for missing work
- Breaking changes or migrations
- Complex refactors
- Agent workflow / validator / CI / Skill / documentation rule changes

For `Size XS/S` and `Risk Low`, use `implementation-prep` alone unless a design decision or intentional omission risk must be recorded beyond TODO / PR / commit notes.

## Documentation Workflow

### 1. Determine Scope

| Condition | Required Documents |
| --- | --- |
| `Size >= M` | Plan, Intent, QA test-plan |
| `Risk >= Medium` | Intent, QA test-plan |
| `Risk High / Critical` | Plan, Intent, QA test-plan, verification before completion |
| Bug with regression risk | QA regression check or no-test rationale |
| Refactor | behavior-preservation checks |
| Intentional omission risk affecting future work | Intent, or Plan Non-Goals when a plan already exists |
| Agent workflow / validator / CI / Skill change | agent misbehavior checks |

### 2. Create or Update Plan

Location: `_docs/plan/<Area>/<slug>/plan.md`

Plan documents should include:

- Overview
- Scope
- Non-Goals
- Requirements
- Tasks
- QA Plan
- Deployment / Rollout

Use root-relative references:

```yaml
references:
  - "_docs/intent/Core/feature-x/decision.md"
  - "_docs/qa/Core/feature-x/test-plan.md"
```

### 3. Create or Update Intent

Location: `_docs/intent/<Area>/<slug>/decision.md`

Intent documents should include:

- `intent_schema: 2`
- Context
- Decisions with stable `DEC-001` style IDs
- `What`, `Why`, and `Change freedom` for each decision
- `Why not` and `Revisit when` only when they add real information
- Consequences / Impact
- Quality Implications
- Intent-derived Invariants only when a condition must remain true across every valid implementation; `None` is normal

Intent documents are permanent rationale records. They constrain future work by
the recorded why and required outcome, not by freezing the current mechanism.
Do not archive intent documents.

### 4. Create QA Test Plan

When creating Plan / Intent for `Size >= M` or `Risk >= Medium`, also run `qa-prep` and create:

```text
_docs/qa/<Area>/<slug>/test-plan.md
```

New QA documents use `qa_schema: 2`, review affected `DEC-*` entries, and may
record `None` when the Intent defines no invariant.

Ensure QA references root-relative canonical paths.

## Integration with Implementation

1. Before coding, confirm Plan / Intent / QA requirements.
2. During implementation, update docs when decisions change.
3. After implementation, run `post-implementation`; for substantial documented work, also run `docs-cleanup`.

## Deliverables

- Plan document when required.
- Intent document when required.
- QA test-plan when required.
- TODO fields updated with canonical paths.
- Front-matter complete with current dates.

## References

- `_docs/standards/documentation_guidelines.md`
- `_docs/standards/documentation_operations.md`
- `_docs/standards/quality_assurance.md`
