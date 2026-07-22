---
name: docs-cleanup
description: Use after post-implementation for Size >= M changes with draft/plan/survey/intent documents.
---

# Documentation Cleanup

This skill finalizes documentation after implementation and enforces archive boundaries.

## When to Use

Use this skill for:

- `Size >= M` changes with documentation
- `Risk >= Medium` changes with QA evidence
- Features with draft / plan / survey / intent documents
- Breaking changes with migration or rollback docs
- Architecture decisions recorded in intent

For `Size XS/S` and `Risk Low`, use `post-implementation` alone unless documentation was created.

## Documentation State Review

Check for:

```text
_docs/draft/<Area>/<slug>/notes.md
_docs/survey/<Area>/<slug>/survey.md
_docs/plan/<Area>/<slug>/plan.md
_docs/intent/<Area>/<slug>/decision.md
_docs/qa/<Area>/<slug>/test-plan.md
_docs/qa/<Area>/<slug>/verification.md
_docs/guide/<Area>/<slug>/usage.md
_docs/reference/<Area>/<slug>/reference.md
```

## QA Document Cleanup

- QA docs are persistent quality records and must not be archived.
- Do not move `_docs/qa/**` into `_docs/archives/**`.
- If a feature is obsolete, mark QA docs as `status: obsolete` or `status: superseded`.
- Keep verification evidence accurate: do not claim commands were run if they were not.

## Archive Rules

Archive only these temporary document types:

```text
_docs/draft/<Area>/<slug>/notes.md
_docs/plan/<Area>/<slug>/plan.md
_docs/survey/<Area>/<slug>/survey.md
```

Do not archive:

- `_docs/intent/**`
- `_docs/qa/**`
- `_docs/guide/**`
- `_docs/reference/**`

## Archive Checklist

Before moving draft / plan / survey into archives:

- Corresponding intent document exists.
- Intent references the temporary document or archive target.
- Archive target has valid front-matter.
- Source directory cleanup is reflected in the diff.
- References are updated to root-relative canonical paths.

Use `mv` or `git mv` only after the checklist passes. Do not use `rm` or `git rm`.

## Guide / Reference Updates

- Create or update guide docs for user-facing usage.
- Create or update reference docs for API or specification details.
- Reference QA verification when user-visible guarantees or residual risks matter.

## Final Verification

Prefer the wrapper:

```bash
./scripts/check-docs.sh
```

When isolating a failure, use the same permissions as the wrapper:

```bash
deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs
deno run --allow-read scripts/validate-todo.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-intent.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.mjs
```

## Deliverables

- Temporary docs archived only when allowed.
- Intent and QA docs kept in live canonical paths.
- Guide / reference updated when needed.
- TODO.md cleaned up only after verification rules pass.
- Validation results recorded.
