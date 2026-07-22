---
title: Fixture intent with orphan invariant
intent_schema: 2
status: active
draft_status: n/a
created_at: 2026-07-17
updated_at: 2026-07-17
references: []
related_issues: []
related_prs: []
fixture_path: "_docs/intent/Workflow/orphan-invariant/decision.md"
---

# Fixture intent with orphan invariant

## Context

This fixture intentionally points an invariant at a missing decision.

## Decisions

### DEC-001: Preserve the observable outcome

- **What**: Keep the externally observable outcome stable.
- **Why**: Consumers depend on the outcome, not the current mechanism.
- **Change freedom**: Internal implementation may change.

## Consequences / Impact

None

## Quality Implications

None

## Intent-derived Invariants

- INV-001 (from DEC-999): The observable outcome remains stable.

## Rollback / Follow-ups

None
