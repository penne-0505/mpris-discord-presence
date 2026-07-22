# Expected Invariants

## Documentation Paths

- `Plan` が必要なタスクは `_docs/plan/<Area>/<slug>/plan.md` を使う。
- QA test-plan は `_docs/qa/<Area>/<slug>/test-plan.md` を使う。
- QA verification は `_docs/qa/<Area>/<slug>/verification.md` を使う。
- `<Area>` は `TODO.md` の `Area` と一致する。
- `<slug>` は機能・変更単位の kebab-case 名にする。
- `intent` は `_docs/intent/<Area>/<slug>/decision.md` に残し、archive しない。
- QA documents are persistent quality records and must not be archived.
- archive 対象は `draft` / `plan` / `survey` のみ。

## TODO.md

- 完了タスクは `TODO.md` から削除する。
- `TODO.md` に Done / Archived セクションを作らない。
- `Size >= M` の Ready / In Progress タスクには実在する Plan が必要。
- `Size < M` のタスクは `Plan: None` を許容する。
- Size >= M tasks require Plan / Intent / QA.
- Risk >= Medium tasks require Intent / QA.
- Intentional omissions that future maintainers could mistake for missing work must be recorded lightly or escalated to Intent.
- High / Critical risk tasks require explicit verification before completion.
- Bug fixes require regression test or no-test rationale.
- Refactors require behavior-preservation checks.
- Agent workflow changes require agent misbehavior checks.
- Tasks with FAIL or BLOCKED verification must not be removed from TODO.md.
- TODO validators must detect malformed or incomplete task headings.

## Safety

- `rm` / `git rm` は使わない。
- archive checklist を満たす一時ドキュメント移送に限り `mv` / `git mv` を使える。
- secret や `.env` 実値を diff / log に出さない。
- Root-level one-off implementation prompts must not be treated as active guidance.
- Template updates use a recommended release tag resolved to a full SHA, not a moving branch tip.
- `docs-template.lock.json` advances only after the target files are reconciled and compatibility checks pass, and closure verification confirms the updated tag and full SHA.
- A pre-`v1.0.0` project may bootstrap directly to any recommended `v1.0.0` or later release after its original template commit is identified; an intermediate migration is not required.
- Compatibility migration and strict schema migration are reported separately.

## Validation

- `deno fmt --check scripts/*.mjs`
- `deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs`
- `deno run --allow-read scripts/validate-todo.mjs`
- `deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs`
- `deno run --allow-read --allow-env --allow-run=git scripts/validate-intent.mjs`
- `deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.mjs`
- `deno run --allow-read --allow-write --allow-env --allow-run scripts/test-validators.mjs`
- `deno run --allow-read --allow-run=git scripts/test-agent-workflow-hook.mjs`
- `deno run --allow-read scripts/test-agent-workflow-smoke.mjs`
- Verification metadata must match the body verdict.
- Validator fixtures must include both valid and intentionally invalid examples.
- New intent records use `intent_schema: 2`, stable `DEC-*` IDs, and causal `Why`.
- `INV-*` is optional and must not freeze a current mechanism or arbitrary value.
