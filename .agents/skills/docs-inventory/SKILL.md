---
name: docs-inventory
description: Use for docs-driven project inventory, stale documentation audit, current-state triage, handoff discovery, or when the user worries docs are drifting, becoming ceremonial, or not being operationally used.
---

# Documentation Inventory

This skill audits whether the docs-driven workflow is still operational. It is diagnostic and read-only by default: produce an inventory report and recommended next actions, but do not archive, delete, or rewrite docs unless the user explicitly asks for follow-up implementation.

## When to Use

Use this skill for:

- Current-state triage after time away from a project.
- Handoff or onboarding discovery when the authoritative doc is unclear.
- A documentation health check, stale-doc audit, or workflow inventory.
- Concern that TODO, intent, QA, guide, or reference docs are valid but no longer operational.
- Before `docs-cleanup` when it is unclear what should be cleaned up.

Do not use this skill for ordinary post-implementation closure. Use `post-implementation` and `qa-review` there.

## Inventory Flow

1. **Find the operating surface.** Read `AGENTS.md`, `TODO.md`, `README.md`, `_docs/documentation_guide.md`, and relevant `_docs/standards/*`. Completion criterion: you can name the current workflow rules and the validation commands.
2. **Map active work.** Inspect `TODO.md` tasks and classify each as ready, blocked, underspecified, or stale. Completion criterion: every active task has a status and the missing Plan / Intent / QA / Verification links are known.
3. **Map durable decisions.** Inspect `_docs/intent/**`, `_docs/qa/**`, `_docs/guide/**`, and `_docs/reference/**`. Completion criterion: each durable doc is tied to active work, completed behavior, or an explicit obsolete / superseded state.
4. **Map temporary docs.** Inspect `_docs/draft/**`, `_docs/survey/**`, and `_docs/plan/**`. Completion criterion: each temporary doc is classified as active, stale, archive candidate, or needs owner decision.
5. **Run validators when available.** Prefer `./scripts/check-docs.sh`; if unavailable, run the closest documented validators. Completion criterion: report the exact commands run, or explain why no command was run.
6. **Separate diagnosis from execution.** Identify cleanup, archive, TODO, QA, or reference actions, but do not perform them in this skill run. Completion criterion: the report lists recommended actions without silently changing the repo.

## Report Shape

Keep the report short and actionable:

- Overall verdict: `Healthy`, `Needs attention`, or `Drifting`.
- Source of truth: which docs currently define active work.
- Findings: ordered by operational impact.
- Inventory table: active tasks, durable docs, temporary docs, and orphan / stale candidates.
- Validation: commands run and result.
- Recommended next actions: one to three actions only.
- Owner decisions needed: questions that require a human choice.

## Classification Rules

- **Ready active work**: TODO task has clear AC, concrete steps, and required Plan / Intent / QA links for its Size / Risk.
- **Underspecified work**: TODO task exists but cannot be acted on without guessing scope, risk, or acceptance criteria.
- **Stale temporary doc**: draft / survey / plan is not referenced by active TODO or recent intent, or its front matter indicates stale status.
- **Archive candidate**: draft / survey / plan has a corresponding intent and references are ready for archive checklist review.
- **Durable doc drift**: intent / QA / guide / reference describes behavior that active code, TODO, or verification no longer supports.
- **Ceremonial doc**: a doc is structurally valid but no active task, completed behavior, test, guide, or decision relies on it.

## Boundaries

- Do not archive intent, QA, guide, or reference docs.
- Do not create Done / Archived sections in `TODO.md`.
- Do not remove completed TODO items unless this inventory becomes an explicit cleanup implementation task.
- Do not treat validator PASS as sufficient health. Validators prove structure, not operational use.
- If cleanup is needed, recommend `docs-cleanup` as the follow-up skill.
