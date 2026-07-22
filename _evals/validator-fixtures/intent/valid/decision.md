---
title: Fixture why-first intent
intent_schema: 2
status: active
draft_status: n/a
created_at: 2026-07-17
updated_at: 2026-07-17
references: []
related_issues: []
related_prs: []
fixture_path: "_docs/intent/Workflow/why-first-fixture/decision.md"
---

# Fixture why-first intent

## Context

The fixture verifies that a decision can preserve rationale without inventing an invariant.

## Decisions

### DEC-001: Keep the rationale as the primary constraint

- **What**: Record the reason and the permitted implementation freedom together.
- **Why**: Future changes need to distinguish the outcome that matters from the current mechanism.
- **Why not**: A bare prohibition would preserve syntax without preserving the reason.
- **Change freedom**: The mechanism may change when the stated outcome remains true.
- **Revisit when**: The outcome itself is intentionally revised.

## Consequences / Impact

Reviewers compare changes with the decision rationale.

## Quality Implications

Acceptance criteria must exercise the outcome rather than a frozen implementation value.

## Intent-derived Invariants

None

## Rollback / Follow-ups

None
