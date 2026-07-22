---
name: post-implementation
description: Use after code changes are complete and before final response or PR summary.
---

# Post-Implementation

This skill closes implementation work by verifying outcomes, updating documentation, and deciding whether TODO items can be removed.

## Closure Flow

1. **Verify completion.** Compare the diff against the original request, TODO Goal, Acceptance Criteria, Intent, and QA test-plan.
2. **Run QA review when required.** If `Size >= M` or `Risk >= Medium`, run `qa-review`.
3. **Update verification.** Ensure `_docs/qa/<Area>/<slug>/verification.md` exists when required.
4. **Decide completion.** Use the verification verdict before removing any TODO item.
5. **Update documentation.** Refresh README, guide, reference, intent, QA, or standards docs as needed.
6. **Summarize changes.** Include validation commands that were actually run and their results.

## Before Removing a Task from TODO.md

- Run `qa-review` if `Size >= M` or `Risk >= Medium`.
- Ensure `verification.md` exists when required.
- Ensure verdict is `PASS`, or `PARTIAL` with explicit follow-up TODOs and accepted residual risk.
- Do not remove TODO items with `FAIL` or `BLOCKED` verification.
- Confirm required intent / guide / reference / QA docs are updated.
- Confirm non-obvious code that encodes a design decision (especially a why not or intentional omission) carries a causal intent anchor (`// intent: DEC-00X (<Area>/<slug>) — <causal why>`) where a future reader could otherwise mistake it for missing or removable work. Use `// intent-invariant: INV-00X ...` only for strict invariants. Targeted, not blanket. See `quality_assurance.md` (intent ↔ code traceability).

## Validation Commands

Prefer the wrapper:

```bash
./scripts/check-docs.sh
```

Use Deno validators, not old npm aliases, when isolating a failure:

```bash
deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs
deno run --allow-read scripts/validate-todo.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-intent.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.mjs
```

## TODO.md Cleanup

- Remove fully completed items from `TODO.md`.
- Keep completion history in PRs, commits, CHANGELOG, intent, guide, reference, or QA verification.
- Do not create Done / Archived sections in `TODO.md`.
- Add follow-up tasks for residual work.

## Deliverables After Implementation

- Verification evidence when required.
- Updated documentation reflecting the current state.
- Updated TODO.md with completed tasks removed and follow-ups added.
- Final summary with validations actually run.
